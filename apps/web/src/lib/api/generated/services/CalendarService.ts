/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BulkStatusRequest } from '../models/BulkStatusRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class CalendarService {
    /**
     * Get Calendar Events
     * @param organizationId
     * @param startDate
     * @param endDate
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getCalendarEventsApiV1CalendarEventsGet(
        organizationId: string,
        startDate: string,
        endDate: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/calendar/events',
            query: {
                'organization_id': organizationId,
                'start_date': startDate,
                'end_date': endDate,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Campaign Overview
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getCampaignOverviewApiV1CampaignsOverviewGet(
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/campaigns/overview',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Bulk Update Status
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static bulkUpdateStatusApiV1CampaignsBulkStatusPost(
        requestBody: BulkStatusRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/campaigns/bulk/status',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
