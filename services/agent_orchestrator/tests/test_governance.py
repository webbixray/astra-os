"""Tests for M3 Governance — approval engine, autonomy enforcement, explainability.

Covers:
  - ApprovalRule evaluation (spend, brand, audience, channel, inactive)
  - ApprovalRequest lifecycle (create, approve, reject, expire, cancel)
  - ApprovalDecision creation (approve, reject validation)
  - AutonomyConfig behavior (get_level, can_auto_execute, overrides)
  - AgentAction recording and explanation
  - AutonomyEnforcementService checks (FULL_AUTO, SEMI_AUTO, ADVISORY)
  - ApprovalEvaluationService rule matching
  - ExplainabilityService output generation
  - AuditEnhancementService hash chain and export

All tests are pure unit tests — no DB, no network required.
"""

import asyncio
import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.domain.common import now
from app.domain.entities.governance.approval import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalRule,
    ApprovalStatus,
    DecisionAction,
    RuleTrigger,
)
from app.domain.entities.governance.autonomy import (
    ACTION_RISK_LEVELS,
    AgentAction,
    AutonomyConfig,
    AutonomyLevel,
    get_action_risk_level,
)
from app.domain.exceptions.domain_exceptions import ValidationError
from app.domain.services.governance.approval_service import (
    ApprovalEvaluationResult,
    ApprovalEvaluationService,
)
from app.domain.services.governance.autonomy_enforcement import (
    AutonomyEnforcementService,
    EnforcementResult,
)
from app.domain.services.governance.explainability import (
    ExplainabilityService,
    ExplanationOutput,
)
from app.domain.services.governance.audit_enhancement import (
    AuditEnhancementService,
    AuditEntry,
)

from app.application.use_cases.governance.approval_use_cases import (
    CreateApprovalRuleUseCase,
    CreateApprovalRequestUseCase,
    DecideApprovalUseCase,
    EvaluateApprovalRulesUseCase,
    ExpireStaleApprovalsUseCase,
    ListPendingApprovalsUseCase,
)
from app.application.use_cases.governance.autonomy_use_cases import (
    CheckAgentActionUseCase,
    GetAutonomyConfigUseCase,
    GetExplainabilityReportUseCase,
    RecordAgentActionUseCase,
    UpdateAutonomyConfigUseCase,
)


# ── Helpers ────────────────────────────────────────────────────────────

ORG_ID = uuid4()


def _spend_rule(min_amount: float = 100.0) -> ApprovalRule:
    return ApprovalRule.create_spend_rule(
        organization_id=ORG_ID,
        name="Spend Rule",
        min_amount=min_amount,
    )


def _brand_rule(keywords: list[str] | None = None) -> ApprovalRule:
    return ApprovalRule.create_brand_rule(
        organization_id=ORG_ID,
        name="Brand Rule",
        keywords=keywords or ["competitor", "guarantee"],
    )


def _audience_rule() -> ApprovalRule:
    return ApprovalRule.create_audience_rule(
        organization_id=ORG_ID,
        name="Audience Rule",
    )


def _channel_rule(channels: list[str] | None = None) -> ApprovalRule:
    return ApprovalRule(
        organization_id=ORG_ID,
        name="Channel Rule",
        trigger=RuleTrigger.CHANNEL_SPECIFIC,
        conditions={"channels": channels or ["ads", "video"]},
    )


# ── Mock Repositories ──────────────────────────────────────────────────


class MockApprovalRuleRepo:
    def __init__(self, rules: list[ApprovalRule] | None = None):
        self._rules = {str(r.id): r for r in (rules or [])}

    async def save(self, rule):
        self._rules[str(rule.id)] = rule
        return rule

    async def find_by_id(self, rule_id):
        return self._rules.get(str(rule_id))

    async def find_by_organization(self, org_id, active_only=True):
        org_id_str = str(org_id)
        rules = [r for r in self._rules.values()
                 if str(r.organization_id) == org_id_str]
        if active_only:
            rules = [r for r in rules if r.is_active]
        return rules

    async def delete(self, rule_id):
        self._rules.pop(str(rule_id), None)


class MockApprovalRequestRepo:
    def __init__(self, requests=None):
        self._requests = {str(r.id): r for r in (requests or [])}

    async def save(self, request):
        self._requests[str(request.id)] = request
        return request

    async def find_by_id(self, request_id):
        return self._requests.get(str(request_id))

    async def find_pending_by_organization(self, org_id):
        return [r for r in self._requests.values()
                if str(r.organization_id) == str(org_id) and r.status == ApprovalStatus.PENDING]

    async def find_pending_by_role(self, org_id, role):
        return [r for r in self._requests.values()
                if str(r.organization_id) == str(org_id)
                and r.status == ApprovalStatus.PENDING
                and r.assigned_role == role]

    async def find_expired_stale(self, before):
        return [r for r in self._requests.values()
                if r.is_pending and r.timeout_at and r.timeout_at < before]


class MockApprovalDecisionRepo:
    def __init__(self):
        self._decisions = {}

    async def save(self, decision):
        self._decisions[str(decision.id)] = decision
        return decision

    async def find_by_request_id(self, request_id):
        for d in self._decisions.values():
            if str(d.request_id) == str(request_id):
                return d
        return None


class MockAutonomyConfigRepo:
    def __init__(self, config=None):
        self._config = config

    async def save(self, config):
        self._config = config
        return config

    async def find_by_organization(self, org_id):
        if self._config and str(self._config.organization_id) == str(org_id):
            return self._config
        return None


class MockAgentActionRepo:
    def __init__(self):
        self._actions = {}

    async def save(self, action):
        self._actions[str(action.id)] = action
        return action

    async def find_by_id(self, action_id):
        return self._actions.get(str(action_id))

    async def find_by_organization(self, org_id, agent_type=None, action_name=None,
                                   limit=50, offset=0):
        results = [a for a in self._actions.values()
                   if str(a.organization_id) == str(org_id)]
        if agent_type:
            results = [a for a in results if a.agent_type == agent_type]
        if action_name:
            results = [a for a in results if a.action == action_name]
        return results[offset:offset + limit]

    async def find_by_agent(self, org_id, agent_id, limit=50):
        return [a for a in self._actions.values()
                if str(a.organization_id) == str(org_id)
                and a.agent_id == agent_id][:limit]


# ══════════════════════════════════════════════════════════════════════
# 1. ApprovalRule Entity Tests
# ══════════════════════════════════════════════════════════════════════


class TestApprovalRule:
    def test_spend_rule_matches_above_threshold(self):
        rule = _spend_rule(min_amount=100.0)
        assert rule.evaluate({"amount": 150.0}) is True

    def test_spend_rule_matches_exact_threshold(self):
        rule = _spend_rule(min_amount=100.0)
        assert rule.evaluate({"amount": 100.0}) is True

    def test_spend_rule_below_threshold(self):
        rule = _spend_rule(min_amount=100.0)
        assert rule.evaluate({"amount": 50.0}) is False

    def test_brand_rule_matches_keyword(self):
        rule = _brand_rule(["competitor"])
        assert rule.evaluate({"text": "Our competitor X is great"}) is True

    def test_brand_rule_no_match(self):
        rule = _brand_rule(["competitor"])
        assert rule.evaluate({"text": "Our product is the best"}) is False

    def test_brand_rule_case_insensitive(self):
        rule = _brand_rule(["guarantee"])
        assert rule.evaluate({"text": "GUARANTEE money back"}) is True

    def test_audience_rule_matches_new_audience(self):
        rule = _audience_rule()
        assert rule.evaluate({"is_new_audience": True}) is True

    def test_audience_rule_no_match_existing(self):
        rule = _audience_rule()
        assert rule.evaluate({"is_new_audience": False}) is False

    def test_channel_rule_matches(self):
        rule = _channel_rule(["ads", "video"])
        assert rule.evaluate({"channel": "ads"}) is True

    def test_channel_rule_no_match(self):
        rule = _channel_rule(["ads"])
        assert rule.evaluate({"channel": "email"}) is False

    def test_inactive_rule_never_matches(self):
        rule = _spend_rule(100.0)
        rule.is_active = False
        assert rule.evaluate({"amount": 9999.0}) is False

    def test_spend_rule_negative_amount_rejected(self):
        with pytest.raises(ValidationError, match="positive"):
            ApprovalRule.create_spend_rule(ORG_ID, "test", min_amount=-10)

    def test_brand_rule_empty_keywords_rejected(self):
        with pytest.raises(ValidationError, match="keyword"):
            ApprovalRule.create_brand_rule(ORG_ID, "test", keywords=[])


# ══════════════════════════════════════════════════════════════════════
# 2. ApprovalRequest Lifecycle Tests
# ══════════════════════════════════════════════════════════════════════


class TestApprovalRequest:
    def _make_request(self) -> ApprovalRequest:
        rule = _spend_rule(100.0)
        return ApprovalRequest.create(
            organization_id=ORG_ID,
            rule=rule,
            action_type="campaign.launch",
            action_resource_id="camp-123",
            action_resource_type="campaign",
            action_summary="Launch campaign with $500 budget",
        )

    def test_create_request(self):
        req = self._make_request()
        assert req.status == ApprovalStatus.PENDING
        assert req.action_type == "campaign.launch"
        assert req.rule_name == "Spend Rule"
        assert req.timeout_at is not None

    def test_approve_request(self):
        req = self._make_request()
        decision = ApprovalDecision.approve(
            request_id=req.id,
            organization_id=ORG_ID,
            decided_by=uuid4(),
        )
        req.approve(decision)
        assert req.status == ApprovalStatus.APPROVED

    def test_reject_request(self):
        req = self._make_request()
        decision = ApprovalDecision.reject(
            request_id=req.id,
            organization_id=ORG_ID,
            decided_by=uuid4(),
            reason="Budget too high",
        )
        req.reject(decision)
        assert req.status == ApprovalStatus.REJECTED

    def test_approve_non_pending_fails(self):
        req = self._make_request()
        decision = ApprovalDecision.approve(req.id, ORG_ID, uuid4())
        req.approve(decision)  # First approve
        with pytest.raises(ValidationError, match="Cannot approve"):
            req.approve(decision)  # Second approve fails

    def test_reject_non_pending_fails(self):
        req = self._make_request()
        decision = ApprovalDecision.reject(req.id, ORG_ID, uuid4(), "no")
        req.reject(decision)
        with pytest.raises(ValidationError, match="Cannot reject"):
            req.reject(decision)

    def test_expire_request(self):
        req = self._make_request()
        req.expire()
        assert req.status == ApprovalStatus.EXPIRED

    def test_cancel_request(self):
        req = self._make_request()
        req.cancel()
        assert req.status == ApprovalStatus.CANCELLED

    def test_cancel_non_pending_fails(self):
        req = self._make_request()
        req.cancel()
        with pytest.raises(ValidationError, match="Cannot cancel"):
            req.cancel()

    def test_is_pending_property(self):
        req = self._make_request()
        assert req.is_pending is True
        req.cancel()
        assert req.is_pending is False


# ══════════════════════════════════════════════════════════════════════
# 3. ApprovalDecision Tests
# ══════════════════════════════════════════════════════════════════════


class TestApprovalDecision:
    def test_approve_factory(self):
        d = ApprovalDecision.approve(uuid4(), ORG_ID, uuid4(), "Looks good")
        assert d.action == DecisionAction.APPROVE
        assert d.reason == "Looks good"

    def test_reject_factory(self):
        d = ApprovalDecision.reject(uuid4(), ORG_ID, uuid4(), "Too risky")
        assert d.action == DecisionAction.REJECT
        assert d.reason == "Too risky"

    def test_reject_without_reason_fails(self):
        with pytest.raises(ValidationError, match="reason is required"):
            ApprovalDecision.reject(uuid4(), ORG_ID, uuid4(), "")


# ══════════════════════════════════════════════════════════════════════
# 4. AutonomyConfig Tests
# ══════════════════════════════════════════════════════════════════════


class TestAutonomyConfig:
    def test_default_advisory(self):
        config = AutonomyConfig.create(ORG_ID)
        assert config.default_level == AutonomyLevel.ADVISORY

    def test_get_level_for_agent_specific(self):
        config = AutonomyConfig.create(ORG_ID, default_level=AutonomyLevel.ADVISORY)
        config.set_agent_level("ContentSpecialist", AutonomyLevel.SEMI_AUTO)
        assert config.get_level_for_agent("ContentSpecialist") == AutonomyLevel.SEMI_AUTO

    def test_get_level_for_agent_fallback(self):
        config = AutonomyConfig.create(ORG_ID, default_level=AutonomyLevel.SEMI_AUTO)
        assert config.get_level_for_agent("UnknownAgent") == AutonomyLevel.SEMI_AUTO

    def test_can_auto_execute_full_auto(self):
        config = AutonomyConfig.create(ORG_ID, default_level=AutonomyLevel.FULL_AUTO)
        assert config.can_auto_execute("campaign.launch") is True

    def test_can_auto_execute_semi_auto_low_risk(self):
        config = AutonomyConfig.create(ORG_ID, default_level=AutonomyLevel.SEMI_AUTO)
        assert config.can_auto_execute("content.generate") is True

    def test_can_auto_execute_semi_auto_high_risk_blocked(self):
        config = AutonomyConfig.create(ORG_ID, default_level=AutonomyLevel.SEMI_AUTO)
        assert config.can_auto_execute("campaign.launch") is False

    def test_can_auto_execute_semi_auto_over_spend_limit(self):
        config = AutonomyConfig.create(
            ORG_ID,
            default_level=AutonomyLevel.SEMI_AUTO,
            auto_approve_spend_limit=100.0,
        )
        assert config.can_auto_execute("bid.update", amount=200.0) is False

    def test_can_auto_execute_advisory_nothing_auto(self):
        config = AutonomyConfig.create(ORG_ID, default_level=AutonomyLevel.ADVISORY)
        assert config.can_auto_execute("content.generate") is False

    def test_get_level_for_action_override_priority(self):
        config = AutonomyConfig.create(ORG_ID, default_level=AutonomyLevel.FULL_AUTO)
        config.action_overrides["campaign.launch"] = AutonomyLevel.ADVISORY
        level = config.get_level_for_action("campaign.launch", "AdvertisingDirector")
        assert level == AutonomyLevel.ADVISORY

    def test_negative_spend_limit_rejected(self):
        with pytest.raises(ValidationError, match="negative"):
            AutonomyConfig.create(ORG_ID, auto_approve_spend_limit=-10)


# ══════════════════════════════════════════════════════════════════════
# 5. AgentAction Tests
# ══════════════════════════════════════════════════════════════════════


class TestAgentAction:
    def test_create_action(self):
        action = AgentAction.create(
            organization_id=ORG_ID,
            agent_id="agent-001",
            agent_type="ContentSpecialist",
            action="content.generate",
        )
        assert action.action == "content.generate"
        assert action.success is True

    def test_record_auto_executed(self):
        action = AgentAction.create(ORG_ID, "a1", "ContentSpecialist", "content.generate")
        action.record_auto_executed(AutonomyLevel.SEMI_AUTO)
        assert action.was_auto_executed is True
        assert action.autonomy_level == AutonomyLevel.SEMI_AUTO

    def test_record_approval_needed(self):
        req_id = uuid4()
        action = AgentAction.create(ORG_ID, "a1", "ContentSpecialist", "campaign.launch")
        action.record_approval_needed(req_id)
        assert action.approval_request_id == req_id
        assert action.was_auto_executed is False

    def test_record_failure(self):
        action = AgentAction.create(ORG_ID, "a1", "ContentSpecialist", "content.generate")
        action.record_failure("Rate limit exceeded")
        assert action.success is False
        assert action.error_message == "Rate limit exceeded"

    def test_add_reasoning_step(self):
        action = AgentAction.create(ORG_ID, "a1", "ContentSpecialist", "content.generate")
        action.add_reasoning_step(1, "Analyzed content requirements", "content.generate", "Success")
        assert len(action.reasoning_trace) == 1
        assert action.reasoning_trace[0]["thought"] == "Analyzed content requirements"

    def test_to_explanation(self):
        action = AgentAction.create(
            ORG_ID, "a1", "ContentSpecialist", "content.generate",
            resource_type="content", resource_id="c-123",
        )
        action.reasoning = "Created based on brand guidelines"
        explanation = action.to_explanation()
        assert "ContentSpecialist" in explanation
        assert "content.generate" in explanation
        assert "brand guidelines" in explanation


# ══════════════════════════════════════════════════════════════════════
# 6. Risk Level Tests
# ══════════════════════════════════════════════════════════════════════


class TestRiskLevels:
    def test_low_risk_actions(self):
        assert get_action_risk_level("content.generate") == 1
        assert get_action_risk_level("analytics.report") == 1
        assert get_action_risk_level("research.analyze") == 1

    def test_high_risk_actions(self):
        assert get_action_risk_level("campaign.launch") == 2
        assert get_action_risk_level("campaign.pause") == 2
        assert get_action_risk_level("spend.allocate") == 2
        assert get_action_risk_level("content.publish") == 2

    def test_unknown_action_defaults_to_low_risk(self):
        assert get_action_risk_level("unknown.action") == 1

    def test_action_risk_levels_has_all_actions(self):
        assert len(ACTION_RISK_LEVELS) >= 20


# ══════════════════════════════════════════════════════════════════════
# 7. ApprovalEvaluationService Tests
# ══════════════════════════════════════════════════════════════════════


class TestApprovalEvaluationService:
    def test_no_rules_no_approval(self):
        svc = ApprovalEvaluationService()
        result = svc.evaluate([], {"amount": 500})
        assert result.requires_approval is False

    def test_spend_rule_triggers(self):
        svc = ApprovalEvaluationService()
        result = svc.evaluate([_spend_rule(100)], {"amount": 200})
        assert result.requires_approval is True
        assert len(result.triggered_rules) == 1

    def test_multiple_rules_triggers(self):
        svc = ApprovalEvaluationService()
        rules = [_spend_rule(100), _brand_rule(["competitor"])]
        ctx = {"amount": 200, "text": "We compete with competitor X"}
        result = svc.evaluate(rules, ctx)
        assert result.requires_approval is True
        assert len(result.triggered_rules) == 2

    def test_evaluate_spend_convenience(self):
        svc = ApprovalEvaluationService()
        result = svc.evaluate_spend([_spend_rule(100)], 200)
        assert result.requires_approval is True

    def test_evaluate_content_convenience(self):
        svc = ApprovalEvaluationService()
        result = svc.evaluate_content([_brand_rule(["guarantee"])], "Money back guarantee")
        assert result.requires_approval is True

    def test_evaluate_channel_convenience(self):
        svc = ApprovalEvaluationService()
        result = svc.evaluate_channel([_channel_rule(["ads"])], "ads")
        assert result.requires_approval is True


# ══════════════════════════════════════════════════════════════════════
# 8. AutonomyEnforcementService Tests
# ══════════════════════════════════════════════════════════════════════


class TestAutonomyEnforcementService:
    def _make_action(self, action_name: str = "content.generate") -> AgentAction:
        return AgentAction.create(ORG_ID, "agent-001", "ContentSpecialist", action_name)

    def test_full_auto_allows_everything(self):
        svc = AutonomyEnforcementService()
        config = AutonomyConfig.create(ORG_ID, default_level=AutonomyLevel.FULL_AUTO)
        action = self._make_action("campaign.launch")
        result = svc.check(config, [], action)
        assert result.allowed is True

    def test_semi_auto_allows_low_risk(self):
        svc = AutonomyEnforcementService()
        config = AutonomyConfig.create(ORG_ID, default_level=AutonomyLevel.SEMI_AUTO)
        action = self._make_action("content.generate")
        result = svc.check(config, [], action)
        assert result.allowed is True

    def test_semi_auto_blocks_high_risk(self):
        svc = AutonomyEnforcementService()
        config = AutonomyConfig.create(ORG_ID, default_level=AutonomyLevel.SEMI_AUTO)
        action = self._make_action("campaign.launch")
        result = svc.check(config, [], action)
        assert result.allowed is False
        assert result.requires_approval is True

    def test_advisory_blocks_everything(self):
        svc = AutonomyEnforcementService()
        config = AutonomyConfig.create(ORG_ID, default_level=AutonomyLevel.ADVISORY)
        action = self._make_action("content.generate")
        result = svc.check(config, [], action)
        assert result.allowed is False
        assert result.requires_approval is True

    def test_semi_auto_over_spend_limit_blocks(self):
        svc = AutonomyEnforcementService()
        config = AutonomyConfig.create(
            ORG_ID,
            default_level=AutonomyLevel.SEMI_AUTO,
            auto_approve_spend_limit=100.0,
        )
        action = self._make_action("bid.update")
        result = svc.check(config, [], action, context={"amount": 200.0})
        assert result.allowed is False

    def test_check_simple_method(self):
        svc = AutonomyEnforcementService()
        config = AutonomyConfig.create(ORG_ID, default_level=AutonomyLevel.SEMI_AUTO)
        result = svc.check_simple(config, "content.generate", "ContentSpecialist", ORG_ID)
        assert result.allowed is True

    def test_enforcement_result_to_dict(self):
        svc = AutonomyEnforcementService()
        config = AutonomyConfig.create(ORG_ID, default_level=AutonomyLevel.ADVISORY)
        action = self._make_action()
        result = svc.check(config, [], action)
        d = result.to_dict()
        assert "allowed" in d
        assert "autonomy_level" in d
        assert "risk_level" in d


# ══════════════════════════════════════════════════════════════════════
# 9. ExplainabilityService Tests
# ══════════════════════════════════════════════════════════════════════


class TestExplainabilityService:
    def test_explain_action(self):
        svc = ExplainabilityService()
        action = AgentAction.create(
            ORG_ID, "agent-001", "ContentSpecialist", "content.generate",
            resource_type="content", resource_id="c-123",
        )
        action.reasoning = "Generated based on brand guidelines"
        output = svc.explain(action)
        assert isinstance(output, ExplanationOutput)
        assert "ContentSpecialist" in output.one_line
        assert "content.generate" in output.paragraph

    def test_generate_summary(self):
        svc = ExplainabilityService()
        action = AgentAction.create(ORG_ID, "a1", "ContentSpecialist", "content.generate")
        summary = svc.generate_summary(action)
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_replay_decision_with_trace(self):
        svc = ExplainabilityService()
        action = AgentAction.create(ORG_ID, "a1", "ContentSpecialist", "content.generate")
        action.add_reasoning_step(1, "Analyzed input", "query", "found data")
        action.add_reasoning_step(2, "Generated content", "generate", "success")
        steps = svc.replay_decision(action)
        assert len(steps) == 2
        assert steps[0]["step"] == 1

    def test_replay_decision_without_trace(self):
        svc = ExplainabilityService()
        action = AgentAction.create(ORG_ID, "a1", "ContentSpecialist", "content.generate")
        steps = svc.replay_decision(action)
        assert len(steps) == 1
        assert steps[0]["step"] == 0

    def test_audit_summary(self):
        svc = ExplainabilityService()
        actions = [
            AgentAction.create(ORG_ID, "a1", "ContentSpecialist", "content.generate"),
            AgentAction.create(ORG_ID, "a2", "AdvertisingDirector", "campaign.launch"),
        ]
        actions[0].record_auto_executed(AutonomyLevel.SEMI_AUTO)
        summary = svc.generate_audit_summary(actions, ORG_ID)
        assert summary["total_actions"] == 2
        assert summary["auto_executed"] == 1
        assert "ContentSpecialist" in summary["by_agent_type"]

    def test_paragraph_with_cost(self):
        svc = ExplainabilityService()
        action = AgentAction.create(ORG_ID, "a1", "ContentSpecialist", "content.generate")
        action.tokens_used = 1500
        action.cost_usd = 0.003
        action.model_used = "llama-3.1-8b"
        paragraph = svc.generate_paragraph(action)
        assert "1,500" in paragraph
        assert "llama-3.1-8b" in paragraph


# ══════════════════════════════════════════════════════════════════════
# 10. AuditEnhancementService Tests
# ══════════════════════════════════════════════════════════════════════


class TestAuditEnhancementService:
    def test_create_entry_has_hash(self):
        svc = AuditEnhancementService()
        entry = svc.create_entry(
            id="entry-1",
            event_type="campaign.activated",
            entity_type="campaign",
            entity_id="c-123",
        )
        assert entry.entry_hash != ""
        assert len(entry.entry_hash) == 64  # SHA-256 hex

    def test_verify_single_entry(self):
        svc = AuditEnhancementService()
        entry = svc.create_entry(
            id="entry-1",
            event_type="campaign.activated",
            entity_type="campaign",
            entity_id="c-123",
        )
        assert svc.verify_single(entry) is True

    def test_verify_tampered_entry_fails(self):
        svc = AuditEnhancementService()
        entry = svc.create_entry(
            id="entry-1",
            event_type="campaign.activated",
            entity_type="campaign",
            entity_id="c-123",
        )
        entry.entry_hash = "tampered"
        assert svc.verify_single(entry) is False

    def test_verify_chain_valid(self):
        svc = AuditEnhancementService()
        e1 = svc.create_entry(
            id="e1", event_type="a", entity_type="b", entity_id="c",
        )
        e2 = svc.create_entry(
            id="e2", event_type="a", entity_type="b", entity_id="d",
            previous_hash=e1.entry_hash,
        )
        e3 = svc.create_entry(
            id="e3", event_type="a", entity_type="b", entity_id="e",
            previous_hash=e2.entry_hash,
        )
        assert svc.verify_chain([e1, e2, e3]) is True

    def test_verify_chain_broken(self):
        svc = AuditEnhancementService()
        e1 = svc.create_entry(
            id="e1", event_type="a", entity_type="b", entity_id="c",
        )
        e2 = svc.create_entry(
            id="e2", event_type="a", entity_type="b", entity_id="d",
            previous_hash="wrong-hash",
        )
        assert svc.verify_chain([e1, e2]) is False

    def test_verify_empty_chain(self):
        svc = AuditEnhancementService()
        assert svc.verify_chain([]) is True

    def test_export_without_pii(self):
        svc = AuditEnhancementService()
        entry = svc.create_entry(
            id="e1", event_type="a", entity_type="b", entity_id="c",
            details={"email": "test@example.com", "action": "create"},
        )
        exported = svc.export_entries([entry], include_pii=False)
        assert exported[0].details.get("email") is None
        assert exported[0].details.get("action") == "create"

    def test_retention_cutoff(self):
        svc = AuditEnhancementService()
        cutoff = svc.get_retention_cutoff(retention_years=7)
        assert cutoff < now()

    def test_should_archive_old_entry(self):
        svc = AuditEnhancementService()
        old_entry = AuditEntry(
            id="old",
            created_at=now() - timedelta(days=365 * 8),
        )
        old_entry.entry_hash = svc.compute_hash(old_entry)
        assert svc.should_archive(old_entry) is True

    def test_generate_export_summary(self):
        svc = AuditEnhancementService()
        entries = [
            svc.create_entry(
                id=f"e{i}", event_type="test.event", entity_type="x", entity_id=f"y{i}",
            )
            for i in range(3)
        ]
        # Link the hash chain properly
        entries[1].previous_hash = entries[0].entry_hash
        entries[1].entry_hash = svc.compute_hash(entries[1])
        entries[2].previous_hash = entries[1].entry_hash
        entries[2].entry_hash = svc.compute_hash(entries[2])
        summary = svc.generate_export_summary(entries, str(ORG_ID))
        assert summary["total_entries"] == 3
        assert summary["chain_valid"] is True


# ══════════════════════════════════════════════════════════════════════
# 11. Use Case Integration Tests (with mock repos)
# ══════════════════════════════════════════════════════════════════════


class TestCreateApprovalRuleUseCase:
    def test_create_spend_rule(self):
        repo = MockApprovalRuleRepo()
        uc = CreateApprovalRuleUseCase(repo)
        rule = asyncio.run(uc.execute(
            organization_id=ORG_ID,
            name="Test Rule",
            trigger=RuleTrigger.SPEND_THRESHOLD,
            conditions={"min_amount": 200},
        ))
        assert rule.name == "Test Rule"
        assert rule.trigger == RuleTrigger.SPEND_THRESHOLD

    def test_empty_name_rejected(self):
        repo = MockApprovalRuleRepo()
        uc = CreateApprovalRuleUseCase(repo)
        with pytest.raises(ValidationError, match="empty"):
            asyncio.run(uc.execute(
                organization_id=ORG_ID,
                name="  ",
                trigger=RuleTrigger.SPEND_THRESHOLD,
            ))

    def test_negative_priority_rejected(self):
        repo = MockApprovalRuleRepo()
        uc = CreateApprovalRuleUseCase(repo)
        with pytest.raises(ValidationError, match="non-negative"):
            asyncio.run(uc.execute(
                organization_id=ORG_ID,
                name="Test",
                trigger=RuleTrigger.SPEND_THRESHOLD,
                priority=-1,
            ))


class TestEvaluateApprovalRulesUseCase:
    def test_evaluate_triggers(self):
        rule = _spend_rule(100)
        repo = MockApprovalRuleRepo([rule])
        uc = EvaluateApprovalRulesUseCase(repo)
        result = asyncio.run(uc.execute(ORG_ID, {"amount": 200}))
        assert result.requires_approval is True

    def test_evaluate_no_match(self):
        rule = _spend_rule(100)
        repo = MockApprovalRuleRepo([rule])
        uc = EvaluateApprovalRulesUseCase(repo)
        result = asyncio.run(uc.execute(ORG_ID, {"amount": 50}))
        assert result.requires_approval is False


class TestDecideApprovalUseCase:
    def test_approve_request(self):
        rule = _spend_rule(100)
        req = ApprovalRequest.create(
            organization_id=ORG_ID, rule=rule,
            action_type="campaign.launch",
            action_resource_id="c1", action_resource_type="campaign",
            action_summary="Launch campaign",
        )
        request_repo = MockApprovalRequestRepo([req])
        decision_repo = MockApprovalDecisionRepo()
        uc = DecideApprovalUseCase(request_repo, decision_repo)

        decision = asyncio.run(uc.execute(
            request_id=req.id,
            decided_by=uuid4(),
            action=DecisionAction.APPROVE,
            reason="Looks good",
        ))
        assert decision.action == DecisionAction.APPROVE

    def test_reject_request(self):
        rule = _spend_rule(100)
        req = ApprovalRequest.create(
            organization_id=ORG_ID, rule=rule,
            action_type="campaign.launch",
            action_resource_id="c1", action_resource_type="campaign",
            action_summary="Launch campaign",
        )
        request_repo = MockApprovalRequestRepo([req])
        decision_repo = MockApprovalDecisionRepo()
        uc = DecideApprovalUseCase(request_repo, decision_repo)

        decision = asyncio.run(uc.execute(
            request_id=req.id,
            decided_by=uuid4(),
            action=DecisionAction.REJECT,
            reason="Too expensive",
        ))
        assert decision.action == DecisionAction.REJECT


class TestCheckAgentActionUseCase:
    def test_check_with_semi_auto(self):
        config = AutonomyConfig.create(
            ORG_ID,
            default_level=AutonomyLevel.SEMI_AUTO,
        )
        config_repo = MockAutonomyConfigRepo(config)
        uc = CheckAgentActionUseCase(config_repo)

        result = asyncio.run(uc.execute(
            organization_id=ORG_ID,
            action_name="content.generate",
            agent_type="ContentSpecialist",
        ))
        assert result.allowed is True

    def test_check_high_risk_blocked(self):
        config = AutonomyConfig.create(
            ORG_ID,
            default_level=AutonomyLevel.SEMI_AUTO,
        )
        config_repo = MockAutonomyConfigRepo(config)
        uc = CheckAgentActionUseCase(config_repo)

        result = asyncio.run(uc.execute(
            organization_id=ORG_ID,
            action_name="campaign.launch",
            agent_type="AdvertisingDirector",
        ))
        assert result.allowed is False

    def test_check_creates_default_config(self):
        config_repo = MockAutonomyConfigRepo(None)
        uc = CheckAgentActionUseCase(config_repo)

        result = asyncio.run(uc.execute(
            organization_id=ORG_ID,
            action_name="content.generate",
            agent_type="ContentSpecialist",
        ))
        # Should create a default ADVISORY config
        assert config_repo._config is not None


class TestRecordAgentActionUseCase:
    def test_record_action(self):
        repo = MockAgentActionRepo()
        uc = RecordAgentActionUseCase(repo)
        action = asyncio.run(uc.execute(
            organization_id=ORG_ID,
            agent_id="agent-001",
            agent_type="ContentSpecialist",
            action_name="content.generate",
            reasoning="Created based on guidelines",
            success=True,
        ))
        assert action.action == "content.generate"
        assert action.success is True

    def test_record_failed_action(self):
        repo = MockAgentActionRepo()
        uc = RecordAgentActionUseCase(repo)
        action = asyncio.run(uc.execute(
            organization_id=ORG_ID,
            agent_id="agent-001",
            agent_type="ContentSpecialist",
            action_name="content.generate",
            success=False,
            error_message="Rate limited",
        ))
        assert action.success is False
        assert action.error_message == "Rate limited"


class TestGetExplainabilityReportUseCase:
    def test_explain_action(self):
        repo = MockAgentActionRepo()
        action = AgentAction.create(
            ORG_ID, "a1", "ContentSpecialist", "content.generate",
            resource_type="content", resource_id="c1",
        )
        asyncio.run(repo.save(action))

        uc = GetExplainabilityReportUseCase(repo)
        explanation = asyncio.run(uc.explain_action(action.id))
        assert isinstance(explanation, ExplanationOutput)
        assert "content.generate" in explanation.paragraph

    def test_generate_audit_summary(self):
        repo = MockAgentActionRepo()
        for i in range(3):
            a = AgentAction.create(
                ORG_ID, f"a{i}", "ContentSpecialist", "content.generate",
            )
            asyncio.run(repo.save(a))

        uc = GetExplainabilityReportUseCase(repo)
        summary = asyncio.run(uc.generate_audit_summary(ORG_ID))
        assert summary["total_actions"] == 3
