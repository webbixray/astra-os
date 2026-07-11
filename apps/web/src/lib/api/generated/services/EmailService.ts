/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { app__presentation__routes__email__email_routes__CreateCampaignRequest } from '../models/app__presentation__routes__email__email_routes__CreateCampaignRequest';
import type { CreateProviderRequest } from '../models/CreateProviderRequest';
import type { RecordEventRequest } from '../models/RecordEventRequest';
import type { SendCampaignRequest } from '../models/SendCampaignRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class EmailService {
    /**
     * Create email provider
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createProviderApiV1EmailProvidersPost(
        requestBody: CreateProviderRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/email/providers',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List email providers
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listProvidersApiV1EmailProvidersGet(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/email/providers',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete email provider
     * @param providerId
     * @param organizationId
     * @returns void
     * @throws ApiError
     */
    public static deleteProviderApiV1EmailProvidersProviderIdDelete(
        providerId: string,
        organizationId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/email/providers/{provider_id}',
            path: {
                'provider_id': providerId,
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
     * Create email campaign
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createEmailCampaignApiV1EmailCampaignsPost(
        requestBody: app__presentation__routes__email__email_routes__CreateCampaignRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/email/campaigns',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List email campaigns
     * @param organizationId
     * @param status
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listEmailCampaignsApiV1EmailCampaignsGet(
        organizationId: string,
        status?: (string | null),
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/email/campaigns',
            query: {
                'organization_id': organizationId,
                'status': status,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get email campaign details
     * @param campaignId
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getEmailCampaignApiV1EmailCampaignsCampaignIdGet(
        campaignId: string,
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/email/campaigns/{campaign_id}',
            path: {
                'campaign_id': campaignId,
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
     * Delete email campaign
     * @param campaignId
     * @param organizationId
     * @returns void
     * @throws ApiError
     */
    public static deleteEmailCampaignApiV1EmailCampaignsCampaignIdDelete(
        campaignId: string,
        organizationId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/email/campaigns/{campaign_id}',
            path: {
                'campaign_id': campaignId,
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
     * Send email campaign
     * @param campaignId
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static sendEmailCampaignApiV1EmailCampaignsCampaignIdSendPost(
        campaignId: string,
        organizationId: string,
        requestBody: SendCampaignRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/email/campaigns/{campaign_id}/send',
            path: {
                'campaign_id': campaignId,
            },
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
     * Get email analytics
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getEmailAnalyticsApiV1EmailAnalyticsGet(
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/email/analytics',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Record email event
     * @param campaignId
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static recordEmailEventApiV1EmailCampaignsCampaignIdEventsPost(
        campaignId: string,
        organizationId: string,
        requestBody: RecordEventRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/email/campaigns/{campaign_id}/events',
            path: {
                'campaign_id': campaignId,
            },
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
     * Get campaign events
     * @param campaignId
     * @param organizationId
     * @param eventType
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getCampaignEventsApiV1EmailCampaignsCampaignIdEventsGet(
        campaignId: string,
        organizationId: string,
        eventType?: (string | null),
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/email/campaigns/{campaign_id}/events',
            path: {
                'campaign_id': campaignId,
            },
            query: {
                'organization_id': organizationId,
                'event_type': eventType,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
