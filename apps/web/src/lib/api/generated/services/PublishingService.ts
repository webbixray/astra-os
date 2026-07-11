/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PublishRequest } from '../models/PublishRequest';
import type { ScheduleRequest } from '../models/ScheduleRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class PublishingService {
    /**
     * Publish content to platform
     * @param contentId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static publishContentApiV1ContentContentIdPublishPost(
        contentId: string,
        requestBody: PublishRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/content/{content_id}/publish',
            path: {
                'content_id': contentId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Schedule content for publishing
     * @param contentId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static scheduleContentApiV1ContentContentIdSchedulePost(
        contentId: string,
        requestBody: ScheduleRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/content/{content_id}/schedule',
            path: {
                'content_id': contentId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get publishing queue
     * @param organizationId
     * @param status
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getPublishingQueueApiV1ContentPublishingQueueGet(
        organizationId: string,
        status?: (string | null),
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/content/publishing/queue',
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
     * Get publishing history
     * @param contentId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getPublishingHistoryApiV1ContentContentIdPublishingHistoryGet(
        contentId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/content/{content_id}/publishing-history',
            path: {
                'content_id': contentId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Retry a failed publish
     * @param publishId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static retryPublishApiV1ContentPublishingPublishIdRetryPost(
        publishId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/content/publishing/{publish_id}/retry',
            path: {
                'publish_id': publishId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Cancel a publishing job
     * @param publishId
     * @returns void
     * @throws ApiError
     */
    public static cancelPublishApiV1ContentPublishingPublishIdDelete(
        publishId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/content/publishing/{publish_id}',
            path: {
                'publish_id': publishId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
