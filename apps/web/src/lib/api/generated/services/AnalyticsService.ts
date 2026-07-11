/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CampaignPerformanceItem } from '../models/CampaignPerformanceItem';
import type { OverviewResponse } from '../models/OverviewResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AnalyticsService {
    /**
     * Get Overview
     * @param organizationId
     * @returns OverviewResponse Successful Response
     * @throws ApiError
     */
    public static getOverviewApiV1AnalyticsOverviewGet(
        organizationId: string,
    ): CancelablePromise<OverviewResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/analytics/overview',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Campaign Performance
     * @param organizationId
     * @returns CampaignPerformanceItem Successful Response
     * @throws ApiError
     */
    public static getCampaignPerformanceApiV1AnalyticsCampaignsGet(
        organizationId: string,
    ): CancelablePromise<Array<CampaignPerformanceItem>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/analytics/campaigns',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Ad Performance
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getAdPerformanceApiV1AnalyticsAdsGet(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/analytics/ads',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
