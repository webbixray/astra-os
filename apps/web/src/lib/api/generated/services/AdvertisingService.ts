/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { app__presentation__routes__advertising__advertising_routes__CreateCampaignRequest } from '../models/app__presentation__routes__advertising__advertising_routes__CreateCampaignRequest';
import type { ConnectAccountRequest } from '../models/ConnectAccountRequest';
import type { CreateCreativeRequest } from '../models/CreateCreativeRequest';
import type { UpdateCreativeRequest } from '../models/UpdateCreativeRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AdvertisingService {
    /**
     * Connect Account
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static connectAccountApiV1AdAccountsPost(
        requestBody: ConnectAccountRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/ad/accounts',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Accounts
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listAccountsApiV1AdAccountsGet(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/ad/accounts',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Disconnect Account
     * @param accountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static disconnectAccountApiV1AdAccountsAccountIdDisconnectPost(
        accountId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/ad/accounts/{account_id}/disconnect',
            path: {
                'account_id': accountId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Sync Account
     * @param accountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static syncAccountApiV1AdAccountsAccountIdSyncPost(
        accountId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/ad/accounts/{account_id}/sync',
            path: {
                'account_id': accountId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Ad Campaign
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createAdCampaignApiV1AdCampaignsPost(
        requestBody: app__presentation__routes__advertising__advertising_routes__CreateCampaignRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/ad/campaigns',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Ad Campaigns
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listAdCampaignsApiV1AdCampaignsGet(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/ad/campaigns',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Sync Campaign
     * @param campaignId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static syncCampaignApiV1AdCampaignsCampaignIdSyncPost(
        campaignId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/ad/campaigns/{campaign_id}/sync',
            path: {
                'campaign_id': campaignId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Creative
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createCreativeApiV1AdCreativesPost(
        requestBody: CreateCreativeRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/ad/creatives',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Creatives
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listCreativesApiV1AdCreativesGet(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/ad/creatives',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Creative
     * @param creativeId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateCreativeApiV1AdCreativesCreativeIdPatch(
        creativeId: string,
        requestBody: UpdateCreativeRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/ad/creatives/{creative_id}',
            path: {
                'creative_id': creativeId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
