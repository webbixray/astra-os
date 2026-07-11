/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AgentRequest } from '../models/AgentRequest';
import type { AgentResponse } from '../models/AgentResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AgentsService {
    /**
     * Process With Agents
     * @param requestBody
     * @returns AgentResponse Successful Response
     * @throws ApiError
     */
    public static processWithAgentsApiV1AgentsProcessPost(
        requestBody: AgentRequest,
    ): CancelablePromise<AgentResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/agents/process',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Agents
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listAgentsApiV1AgentsGet(): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/agents',
        });
    }
    /**
     * List Tools
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listToolsApiV1AgentsToolsGet(): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/agents/tools',
        });
    }
}
