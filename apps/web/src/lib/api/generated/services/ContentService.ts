/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ContentResponse } from '../models/ContentResponse';
import type { CreateContentRequest } from '../models/CreateContentRequest';
import type { PaginatedResponse_ContentResponse_ } from '../models/PaginatedResponse_ContentResponse_';
import type { UpdateContentRequest } from '../models/UpdateContentRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ContentService {
    /**
     * Create new content
     * @param requestBody
     * @returns ContentResponse Successful Response
     * @throws ApiError
     */
    public static createContentApiV1ContentPost(
        requestBody: CreateContentRequest,
    ): CancelablePromise<ContentResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/content',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List content items
     * @param organizationId
     * @param status
     * @param page
     * @param limit
     * @returns PaginatedResponse_ContentResponse_ Successful Response
     * @throws ApiError
     */
    public static listContentApiV1ContentGet(
        organizationId: string,
        status?: (string | null),
        page: number = 1,
        limit: number = 50,
    ): CancelablePromise<PaginatedResponse_ContentResponse_> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/content',
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
     * Get content by ID
     * @param contentId
     * @returns ContentResponse Successful Response
     * @throws ApiError
     */
    public static getContentApiV1ContentContentIdGet(
        contentId: string,
    ): CancelablePromise<ContentResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/content/{content_id}',
            path: {
                'content_id': contentId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update content by ID
     * @param contentId
     * @param requestBody
     * @returns ContentResponse Successful Response
     * @throws ApiError
     */
    public static updateContentApiV1ContentContentIdPatch(
        contentId: string,
        requestBody: UpdateContentRequest,
    ): CancelablePromise<ContentResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/content/{content_id}',
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
}
