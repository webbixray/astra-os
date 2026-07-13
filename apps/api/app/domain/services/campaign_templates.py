"""Sample Campaign Templates — E6.3 Self-Serve Starter.

Pre-built campaign templates for new user onboarding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from app.domain.entities.campaign import Campaign, CampaignObjective, CampaignStatus


@dataclass
class CampaignTemplate:
    """A pre-built campaign template for onboarding."""

    name: str
    description: str
    objective: CampaignObjective
    targeting: dict[str, Any]
    budget: float
    creative_concepts: list[dict[str, str]]
    tags: list[str] = field(default_factory=list)


# Built-in campaign templates
CAMPAIGN_TEMPLATES: list[CampaignTemplate] = [
    CampaignTemplate(
        name="Brand Awareness Launch",
        description="Introduce your brand to new audiences with broad reach",
        objective=CampaignObjective.BRAND_AWARENESS,
        budget=5000.0,
        targeting={
            "age_min": 25,
            "age_max": 55,
            "interests": ["technology", "business", "innovation"],
            "locations": ["US", "CA", "UK"],
        },
        creative_concepts=[
            {
                "headline": "Introducing the Future of {industry}",
                "body": "Discover how {brand} is transforming {industry} with innovative solutions.",
                "cta": "Learn More",
            },
            {
                "headline": "Why {brand} is Different",
                "body": "See what makes our approach unique. Join thousands of satisfied customers.",
                "cta": "Explore",
            },
        ],
        tags=["awareness", "launch", "broad-reach"],
    ),
    CampaignTemplate(
        name="Lead Generation Funnel",
        description="Capture high-quality leads with targeted content offers",
        objective=CampaignObjective.LEAD_GENERATION,
        budget=3000.0,
        targeting={
            "job_titles": ["CTO", "VP Engineering", "Director", "Manager"],
            "company_size": ["50-200", "200-500", "500+"],
            "interests": ["saas", "productivity", "automation"],
            "locations": ["US", "CA"],
        },
        creative_concepts=[
            {
                "headline": "Free Guide: {topic} Best Practices",
                "body": "Download our comprehensive guide to mastering {topic}. Trusted by 10,000+ professionals.",
                "cta": "Download Free",
            },
            {
                "headline": "Webinar: Mastering {topic}",
                "body": "Join our live session with industry experts. Limited seats available.",
                "cta": "Register Now",
            },
        ],
        tags=["leads", "content", "funnel"],
    ),
    CampaignTemplate(
        name="Product Launch Campaign",
        description="Drive conversions for your new product launch",
        objective=CampaignObjective.CONVERSIONS,
        budget=4000.0,
        targeting={
            "interests": ["technology", "innovation", "startups"],
            "behaviors": ["early_adopters", "tech_enthusiasts"],
            "age_range": [25, 45],
            "locations": ["US", "CA", "AU", "UK"],
        },
        creative_concepts=[
            {
                "headline": "Introducing {product_name}",
                "body": "The {category} you've been waiting for. Pre-order now for exclusive early-bird pricing.",
                "cta": "Pre-Order",
            },
            {
                "headline": "{product_name} is Here",
                "body": "Join 5,000+ beta users who've already transformed their workflow.",
                "cta": "Get Started",
            },
        ],
        tags=["product-launch", "conversions", "urgency"],
    ),
    CampaignTemplate(
        name="Retargeting & Retention",
        description="Re-engage past visitors and nurture existing customers",
        objective=CampaignObjective.ENGAGEMENT,
        budget=2000.0,
        targeting={
            "custom_audiences": ["website_visitors_30d", "cart_abandoners", "past_customers"],
            "exclusions": ["recent_purchasers_7d"],
        },
        creative_concepts=[
            {
                "headline": "Still Interested in {product}?",
                "body": "You left something behind. Complete your purchase and get 15% off.",
                "cta": "Complete Purchase",
            },
            {
                "headline": "We Miss You!",
                "body": "It's been a while. Here's a special offer to welcome you back.",
                "cta": "Claim Offer",
            },
        ],
        tags=["retargeting", "retention", "recovery"],
    ),
    CampaignTemplate(
        name="Thought Leadership Content",
        description="Establish authority with educational content series",
        objective=CampaignObjective.BRAND_AWARENESS,
        budget=1500.0,
        targeting={
            "job_titles": ["CEO", "CTO", "VP", "Director", "Founder"],
            "industries": ["technology", "finance", "healthcare", "manufacturing"],
            "seniority": ["director", "vp", "c_level"],
        },
        creative_concepts=[
            {
                "headline": "The State of {industry} 2024",
                "body": "Our annual report reveals key trends shaping the future. Download free.",
                "cta": "Get Report",
            },
            {
                "headline": "How {company} Solved {problem}",
                "body": "Case study: See how we helped {company} achieve {result} in 90 days.",
                "cta": "Read Case Study",
            },
        ],
        tags=["thought-leadership", "content", "authority"],
    ),
]


def get_templates_for_onboarding(
    count: int = 3,
    objectives: list[CampaignObjective] | None = None,
) -> list[CampaignTemplate]:
    """Select templates for onboarding based on count and objectives."""
    templates = CAMPAIGN_TEMPLATES

    if objectives:
        templates = [t for t in templates if t.objective in objectives]

    # Sort by relevance (awareness first, then leads, then conversions)
    priority_order = {
        CampaignObjective.BRAND_AWARENESS: 0,
        CampaignObjective.LEAD_GENERATION: 1,
        CampaignObjective.CONVERSIONS: 2,
        CampaignObjective.ENGAGEMENT: 3,
    }
    templates.sort(key=lambda t: priority_order.get(t.objective, 99))

    return templates[:count]


def create_campaign_from_template(
    template: CampaignTemplate,
    organization_id: str,
    created_by: str,
    customizations: dict[str, Any] | None = None,
) -> Campaign:
    """Create a Campaign entity from a template with optional customizations."""
    c = customizations or {}

    campaign = Campaign.create(
        organization_id=uuid4(),
        name=c.get("name", template.name),
        objective=template.objective,
        created_by=uuid4(),
        description=c.get("description", template.description),
        total_budget=c.get("budget", template.budget),
        targeting={**template.targeting, **c.get("targeting", {})},
        status=CampaignStatus.DRAFT,
    )

    # Store template metadata
    campaign.metadata = {
        "template_id": template.name.lower().replace(" ", "-"),
        "creative_concepts": template.creative_concepts,
        "tags": template.tags,
    }

    return campaign


def get_template_by_name(name: str) -> CampaignTemplate | None:
    """Find a template by name (case-insensitive)."""
    name_lower = name.lower().replace(" ", "-")
    for template in CAMPAIGN_TEMPLATES:
        if template.name.lower().replace(" ", "-") == name_lower:
            return template
    return None


def list_all_templates() -> list[dict[str, Any]]:
    """Get summary of all available templates."""
    return [
        {
            "id": t.name.lower().replace(" ", "-"),
            "name": t.name,
            "description": t.description,
            "objective": t.objective.value,
            "budget": t.budget,
            "tags": t.tags,
        }
        for t in CAMPAIGN_TEMPLATES
    ]