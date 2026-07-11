/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AddVariantRequest } from '../models/AddVariantRequest';
import type { app__presentation__routes__campaigns__campaign_routes__CreateCampaignRequest } from '../models/app__presentation__routes__campaigns__campaign_routes__CreateCampaignRequest';
import type { app__presentation__routes__campaigns__campaign_routes__CreateTemplateRequest } from '../models/app__presentation__routes__campaigns__campaign_routes__CreateTemplateRequest';
import type { CampaignResponse } from '../models/CampaignResponse';
import type { CloneFromTemplateRequest } from '../models/CloneFromTemplateRequest';
import type { CreateABTestRequest } from '../models/CreateABTestRequest';
import type { PaginatedResponse_CampaignResponse_ } from '../models/PaginatedResponse_CampaignResponse_';
import type { RecordMetricsRequest } from '../models/RecordMetricsRequest';
import type { RecordSpendRequest } from '../models/RecordSpendRequest';
import type { SetBudgetRequest } from '../models/SetBudgetRequest';
import type { UpdateCampaignRequest } from '../models/UpdateCampaignRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class CampaignsService {
    /**
     * Create a new campaign
     * @param requestBody
     * @returns CampaignResponse Successful Response
     * @throws ApiError
     */
    public static createCampaignApiV1CampaignsPost(
        requestBody: app__presentation__routes__campaigns__campaign_routes__CreateCampaignRequest,
    ): CancelablePromise<CampaignResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/campaigns',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List all campaigns
     * @param organizationId
     * @param status
     * @param page
     * @param limit
     * @returns PaginatedResponse_CampaignResponse_ Successful Response
     * @throws ApiError
     */
    public static listCampaignsApiV1CampaignsGet(
        organizationId: string,
        status?: (string | null),
        page: number = 1,
        limit: number = 50,
    ): CancelablePromise<PaginatedResponse_CampaignResponse_> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/campaigns',
            query: {
                'organization_id': organizationId,
                'status': status,
                'page': page,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get a campaign by ID
     * @param campaignId
     * @returns CampaignResponse Successful Response
     * @throws ApiError
     */
    public static getCampaignApiV1CampaignsCampaignIdGet(
        campaignId: string,
    ): CancelablePromise<CampaignResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/campaigns/{campaign_id}',
            path: {
                'campaign_id': campaignId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update a campaign
     * @param campaignId
     * @param requestBody
     * @returns CampaignResponse Successful Response
     * @throws ApiError
     */
    public static updateCampaignApiV1CampaignsCampaignIdPatch(
        campaignId: string,
        requestBody: UpdateCampaignRequest,
    ): CancelablePromise<CampaignResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/campaigns/{campaign_id}',
            path: {
                'campaign_id': campaignId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get campaign budget details
     * @param campaignId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getCampaignBudgetApiV1CampaignsCampaignIdBudgetGet(
        campaignId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/campaigns/{campaign_id}/budget',
            path: {
                'campaign_id': campaignId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Set campaign budget
     * @param campaignId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static setCampaignBudgetApiV1CampaignsCampaignIdBudgetPut(
        campaignId: string,
        requestBody: SetBudgetRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/campaigns/{campaign_id}/budget',
            path: {
                'campaign_id': campaignId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Record campaign spend
     * @param campaignId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static recordCampaignSpendApiV1CampaignsCampaignIdBudgetSpendPost(
        campaignId: string,
        requestBody: RecordSpendRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/campaigns/{campaign_id}/budget/spend',
            path: {
                'campaign_id': campaignId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create a campaign template
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createTemplateApiV1CampaignsTemplatesPost(
        requestBody: app__presentation__routes__campaigns__campaign_routes__CreateTemplateRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/campaigns/templates',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List all campaign templates
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listTemplatesApiV1CampaignsTemplatesGet(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/campaigns/templates',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get a template by ID
     * @param templateId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getTemplateApiV1CampaignsTemplatesTemplateIdGet(
        templateId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/campaigns/templates/{template_id}',
            path: {
                'template_id': templateId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete a campaign template
     * @param templateId
     * @returns void
     * @throws ApiError
     */
    public static deleteTemplateApiV1CampaignsTemplatesTemplateIdDelete(
        templateId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/campaigns/templates/{template_id}',
            path: {
                'template_id': templateId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Clone campaign from template
     * @param requestBody
     * @returns CampaignResponse Successful Response
     * @throws ApiError
     */
    public static cloneFromTemplateApiV1CampaignsFromTemplatePost(
        requestBody: CloneFromTemplateRequest,
    ): CancelablePromise<CampaignResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/campaigns/from-template',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create an A/B test
     * @param campaignId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createAbTestApiV1CampaignsCampaignIdAbTestsPost(
        campaignId: string,
        requestBody: CreateABTestRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/campaigns/{campaign_id}/ab-tests',
            path: {
                'campaign_id': campaignId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List A/B tests for campaign
     * @param campaignId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listAbTestsApiV1CampaignsCampaignIdAbTestsGet(
        campaignId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/campaigns/{campaign_id}/ab-tests',
            path: {
                'campaign_id': campaignId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get A/B test details
     * @param testId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getAbTestApiV1CampaignsAbTestsTestIdGet(
        testId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/campaigns/ab-tests/{test_id}',
            path: {
                'test_id': testId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Add variant to A/B test
     * @param testId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static addVariantApiV1CampaignsAbTestsTestIdVariantsPost(
        testId: string,
        requestBody: AddVariantRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/campaigns/ab-tests/{test_id}/variants',
            path: {
                'test_id': testId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Start an A/B test
     * @param testId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static startAbTestApiV1CampaignsAbTestsTestIdStartPost(
        testId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/campaigns/ab-tests/{test_id}/start',
            path: {
                'test_id': testId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Determine A/B test winner
     * @param testId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static determineWinnerApiV1CampaignsAbTestsTestIdDetermineWinnerPost(
        testId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/campaigns/ab-tests/{test_id}/determine-winner',
            path: {
                'test_id': testId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Record variant metrics
     * @param testId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static recordVariantMetricsApiV1CampaignsAbTestsTestIdMetricsPost(
        testId: string,
        requestBody: RecordMetricsRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/campaigns/ab-tests/{test_id}/metrics',
            path: {
                'test_id': testId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
