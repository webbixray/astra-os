/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CreatePromptRequest } from '../models/CreatePromptRequest';
import type { PromptResponse } from '../models/PromptResponse';
import type { UpdatePromptRequest } from '../models/UpdatePromptRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class PromptsService {
    /**
     * List all prompts
     * @param category
     * @param orgId
     * @returns PromptResponse Successful Response
     * @throws ApiError
     */
    public static listPromptsApiV1PromptsGet(
        category?: (string | null),
        orgId?: (string | null),
    ): CancelablePromise<Array<PromptResponse>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/prompts',
            query: {
                'category': category,
                'org_id': orgId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create a new prompt
     * @param requestBody
     * @returns PromptResponse Successful Response
     * @throws ApiError
     */
    public static createPromptApiV1PromptsPost(
        requestBody: CreatePromptRequest,
    ): CancelablePromise<PromptResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/prompts',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List built-in prompts
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listBuiltinsApiV1PromptsBuiltinsGet(): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/prompts/builtins',
        });
    }
    /**
     * Get prompt by ID
     * @param promptId
     * @param organizationId
     * @returns PromptResponse Successful Response
     * @throws ApiError
     */
    public static getPromptApiV1PromptsPromptIdGet(
        promptId: string,
        organizationId: string,
    ): CancelablePromise<PromptResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/prompts/{prompt_id}',
            path: {
                'prompt_id': promptId,
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
     * Update a prompt
     * @param promptId
     * @param organizationId
     * @param requestBody
     * @returns PromptResponse Successful Response
     * @throws ApiError
     */
    public static updatePromptApiV1PromptsPromptIdPatch(
        promptId: string,
        organizationId: string,
        requestBody: UpdatePromptRequest,
    ): CancelablePromise<PromptResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/prompts/{prompt_id}',
            path: {
                'prompt_id': promptId,
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
     * Delete a prompt
     * @param promptId
     * @param organizationId
     * @returns void
     * @throws ApiError
     */
    public static deletePromptApiV1PromptsPromptIdDelete(
        promptId: string,
        organizationId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/prompts/{prompt_id}',
            path: {
                'prompt_id': promptId,
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
