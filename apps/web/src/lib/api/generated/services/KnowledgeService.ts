/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CreateNodeRequest } from '../models/CreateNodeRequest';
import type { CreateRelationRequest } from '../models/CreateRelationRequest';
import type { RecallRequest } from '../models/RecallRequest';
import type { RememberRequest } from '../models/RememberRequest';
import type { SearchRequest } from '../models/SearchRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class KnowledgeService {
    /**
     * Create Node
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createNodeApiV1KnowledgeNodesPost(
        requestBody: CreateNodeRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/knowledge/nodes',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Search Knowledge
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static searchKnowledgeApiV1KnowledgeSearchPost(
        requestBody: SearchRequest,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/knowledge/search',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Relation
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createRelationApiV1KnowledgeRelationsPost(
        requestBody: CreateRelationRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/knowledge/relations',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Node Relations
     * @param nodeId
     * @param relationType
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getNodeRelationsApiV1KnowledgeNodesNodeIdRelationsGet(
        nodeId: string,
        relationType?: (string | null),
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/knowledge/nodes/{node_id}/relations',
            path: {
                'node_id': nodeId,
            },
            query: {
                'relation_type': relationType,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Remember
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static rememberApiV1KnowledgeMemoryRememberPost(
        requestBody: RememberRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/knowledge/memory/remember',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Recall
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static recallApiV1KnowledgeMemoryRecallPost(
        requestBody: RecallRequest,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/knowledge/memory/recall',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Memories
     * @param organizationId
     * @param userId
     * @param type
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getMemoriesApiV1KnowledgeMemoryOrganizationIdUserIdGet(
        organizationId: string,
        userId: string,
        type?: (string | null),
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/knowledge/memory/{organization_id}/{user_id}',
            path: {
                'organization_id': organizationId,
                'user_id': userId,
            },
            query: {
                'type': type,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
