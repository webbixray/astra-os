/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CreateWorkflowRequest } from '../models/CreateWorkflowRequest';
import type { ExecuteWorkflowRequest } from '../models/ExecuteWorkflowRequest';
import type { UpdateWorkflowRequest } from '../models/UpdateWorkflowRequest';
import type { WorkflowResponse } from '../models/WorkflowResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class WorkflowsService {
    /**
     * Create a new workflow
     * @param requestBody
     * @returns WorkflowResponse Successful Response
     * @throws ApiError
     */
    public static createWorkflowApiV1WorkflowsPost(
        requestBody: CreateWorkflowRequest,
    ): CancelablePromise<WorkflowResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/workflows',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List all workflows
     * @param organizationId
     * @param status
     * @returns WorkflowResponse Successful Response
     * @throws ApiError
     */
    public static listWorkflowsApiV1WorkflowsGet(
        organizationId: string,
        status?: (string | null),
    ): CancelablePromise<Array<WorkflowResponse>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/workflows',
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
     * Get workflow by ID
     * @param workflowId
     * @returns WorkflowResponse Successful Response
     * @throws ApiError
     */
    public static getWorkflowApiV1WorkflowsWorkflowIdGet(
        workflowId: string,
    ): CancelablePromise<WorkflowResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/workflows/{workflow_id}',
            path: {
                'workflow_id': workflowId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update a workflow
     * @param workflowId
     * @param requestBody
     * @returns WorkflowResponse Successful Response
     * @throws ApiError
     */
    public static updateWorkflowApiV1WorkflowsWorkflowIdPatch(
        workflowId: string,
        requestBody: UpdateWorkflowRequest,
    ): CancelablePromise<WorkflowResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/workflows/{workflow_id}',
            path: {
                'workflow_id': workflowId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Execute a workflow
     * @param workflowId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static executeWorkflowApiV1WorkflowsWorkflowIdExecutePost(
        workflowId: string,
        requestBody: ExecuteWorkflowRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/workflows/{workflow_id}/execute',
            path: {
                'workflow_id': workflowId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List workflow executions
     * @param workflowId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listExecutionsApiV1WorkflowsWorkflowIdExecutionsGet(
        workflowId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/workflows/{workflow_id}/executions',
            path: {
                'workflow_id': workflowId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
