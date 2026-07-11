/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CreateBidRuleRequest } from '../models/CreateBidRuleRequest';
import type { CreateBudgetRuleRequest } from '../models/CreateBudgetRuleRequest';
import type { CreateRuleRequest } from '../models/CreateRuleRequest';
import type { CreateSegmentRequest } from '../models/CreateSegmentRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AutomationService {
    /**
     * Create a budget allocation rule
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createBudgetRuleApiV1AutomationBudgetRulesPost(
        organizationId: string,
        requestBody: CreateBudgetRuleRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/automation/budget-rules',
            query: {
                'organization_id': organizationId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List budget allocation rules
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listBudgetRulesApiV1AutomationBudgetRulesGet(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/automation/budget-rules',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Calculate budget allocation
     * @param ruleId
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static calculateAllocationApiV1AutomationBudgetRulesRuleIdCalculatePost(
        ruleId: string,
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/automation/budget-rules/{rule_id}/calculate',
            path: {
                'rule_id': ruleId,
            },
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete a budget rule
     * @param ruleId
     * @param organizationId
     * @returns void
     * @throws ApiError
     */
    public static deleteBudgetRuleApiV1AutomationBudgetRulesRuleIdDelete(
        ruleId: string,
        organizationId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/automation/budget-rules/{rule_id}',
            path: {
                'rule_id': ruleId,
            },
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create a bid optimization rule
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createBidRuleApiV1AutomationBidRulesPost(
        organizationId: string,
        requestBody: CreateBidRuleRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/automation/bid-rules',
            query: {
                'organization_id': organizationId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List bid optimization rules
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listBidRulesApiV1AutomationBidRulesGet(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/automation/bid-rules',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Optimize bid for rule
     * @param ruleId
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static optimizeBidApiV1AutomationBidRulesRuleIdOptimizePost(
        ruleId: string,
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/automation/bid-rules/{rule_id}/optimize',
            path: {
                'rule_id': ruleId,
            },
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete a bid rule
     * @param ruleId
     * @param organizationId
     * @returns void
     * @throws ApiError
     */
    public static deleteBidRuleApiV1AutomationBidRulesRuleIdDelete(
        ruleId: string,
        organizationId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/automation/bid-rules/{rule_id}',
            path: {
                'rule_id': ruleId,
            },
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create an audience segment
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createAudienceSegmentApiV1AutomationAudienceSegmentsPost(
        organizationId: string,
        requestBody: CreateSegmentRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/automation/audience-segments',
            query: {
                'organization_id': organizationId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List audience segments
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listAudienceSegmentsApiV1AutomationAudienceSegmentsGet(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/automation/audience-segments',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Predict audience size
     * @param segmentId
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static predictAudienceApiV1AutomationAudienceSegmentsSegmentIdPredictPost(
        segmentId: string,
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/automation/audience-segments/{segment_id}/predict',
            path: {
                'segment_id': segmentId,
            },
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete an audience segment
     * @param segmentId
     * @param organizationId
     * @returns void
     * @throws ApiError
     */
    public static deleteAudienceSegmentApiV1AutomationAudienceSegmentsSegmentIdDelete(
        segmentId: string,
        organizationId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/automation/audience-segments/{segment_id}',
            path: {
                'segment_id': segmentId,
            },
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Generate content recommendations
     * @param organizationId
     * @param campaignId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static generateRecommendationsApiV1AutomationRecommendationsGeneratePost(
        organizationId: string,
        campaignId?: (string | null),
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/automation/recommendations/generate',
            query: {
                'organization_id': organizationId,
                'campaign_id': campaignId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List content recommendations
     * @param organizationId
     * @param type
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listRecommendationsApiV1AutomationRecommendationsGet(
        organizationId: string,
        type?: (string | null),
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/automation/recommendations',
            query: {
                'organization_id': organizationId,
                'type': type,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Apply a recommendation
     * @param recId
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static applyRecommendationApiV1AutomationRecommendationsRecIdApplyPost(
        recId: string,
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/automation/recommendations/{rec_id}/apply',
            path: {
                'rec_id': recId,
            },
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create an automation rule
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createAutomationRuleApiV1AutomationRulesPost(
        organizationId: string,
        requestBody: CreateRuleRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/automation/rules',
            query: {
                'organization_id': organizationId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List automation rules
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listAutomationRulesApiV1AutomationRulesGet(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/automation/rules',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Toggle automation rule enabled state
     * @param ruleId
     * @param enabled
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static toggleAutomationRuleApiV1AutomationRulesRuleIdTogglePatch(
        ruleId: string,
        enabled: boolean,
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/automation/rules/{rule_id}/toggle',
            path: {
                'rule_id': ruleId,
            },
            query: {
                'enabled': enabled,
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Evaluate all automation rules
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static evaluateAutomationRulesApiV1AutomationRulesEvaluatePost(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/automation/rules/evaluate',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete an automation rule
     * @param ruleId
     * @param organizationId
     * @returns void
     * @throws ApiError
     */
    public static deleteAutomationRuleApiV1AutomationRulesRuleIdDelete(
        ruleId: string,
        organizationId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/automation/rules/{rule_id}',
            path: {
                'rule_id': ruleId,
            },
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
