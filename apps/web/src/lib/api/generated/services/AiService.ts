/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChatRequestSchema } from '../models/ChatRequestSchema';
import type { ChatResponse } from '../models/ChatResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AiService {
    /**
     * Stream chat response
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static chatStreamApiV1ChatStreamPost(
        requestBody: ChatRequestSchema,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/chat/stream',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Send a chat message
     * @param requestBody
     * @returns ChatResponse Successful Response
     * @throws ApiError
     */
    public static chatApiV1ChatPost(
        requestBody: ChatRequestSchema,
    ): CancelablePromise<ChatResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/chat',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
