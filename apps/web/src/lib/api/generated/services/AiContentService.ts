/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BrandVoiceCreate } from '../models/BrandVoiceCreate';
import type { BrandVoiceUpdate } from '../models/BrandVoiceUpdate';
import type { BulkGenerateRequest } from '../models/BulkGenerateRequest';
import type { GenerateRequest } from '../models/GenerateRequest';
import type { PaginatedResponse } from '../models/PaginatedResponse';
import type { RewriteRequest } from '../models/RewriteRequest';
import type { SEOScoreRequest } from '../models/SEOScoreRequest';
import type { TemplateCreate } from '../models/TemplateCreate';
import type { TemplateUpdate } from '../models/TemplateUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AiContentService {
    /**
     * Generate AI content
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static generateContentApiV1AiContentGeneratePost(
        requestBody: GenerateRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/ai/content/generate',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Rewrite content with AI
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static rewriteContentApiV1AiContentRewritePost(
        requestBody: RewriteRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/ai/content/rewrite',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Bulk generate AI content
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static bulkGenerateApiV1AiContentGenerateBulkPost(
        requestBody: BulkGenerateRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/ai/content/generate/bulk',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Score content for SEO
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static scoreContentApiV1AiContentSeoScorePost(
        requestBody: SEOScoreRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/ai/content/seo-score',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create a brand voice
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createBrandVoiceApiV1BrandVoicesPost(
        requestBody: BrandVoiceCreate,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/brand-voices',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List brand voices
     * @param organizationId
     * @param page
     * @param limit
     * @returns PaginatedResponse Successful Response
     * @throws ApiError
     */
    public static listBrandVoicesApiV1BrandVoicesGet(
        organizationId: string,
        page: number = 1,
        limit: number = 50,
    ): CancelablePromise<PaginatedResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/brand-voices',
            query: {
                'organization_id': organizationId,
                'page': page,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update a brand voice
     * @param voiceId
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateBrandVoiceApiV1BrandVoicesVoiceIdPatch(
        voiceId: string,
        organizationId: string,
        requestBody: BrandVoiceUpdate,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/brand-voices/{voice_id}',
            path: {
                'voice_id': voiceId,
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
     * Delete a brand voice
     * @param voiceId
     * @param organizationId
     * @returns void
     * @throws ApiError
     */
    public static deleteBrandVoiceApiV1BrandVoicesVoiceIdDelete(
        voiceId: string,
        organizationId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/brand-voices/{voice_id}',
            path: {
                'voice_id': voiceId,
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
     * Create a content template
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createTemplateApiV1ContentTemplatesPost(
        requestBody: TemplateCreate,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/content/templates',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List content templates
     * @param organizationId
     * @param includeBuiltin
     * @param page
     * @param limit
     * @returns PaginatedResponse Successful Response
     * @throws ApiError
     */
    public static listTemplatesApiV1ContentTemplatesGet(
        organizationId: string,
        includeBuiltin: boolean = true,
        page: number = 1,
        limit: number = 50,
    ): CancelablePromise<PaginatedResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/content/templates',
            query: {
                'organization_id': organizationId,
                'include_builtin': includeBuiltin,
                'page': page,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get a content template
     * @param templateId
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getTemplateApiV1ContentTemplatesTemplateIdGet(
        templateId: string,
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/content/templates/{template_id}',
            path: {
                'template_id': templateId,
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
     * Update a content template
     * @param templateId
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateTemplateApiV1ContentTemplatesTemplateIdPatch(
        templateId: string,
        organizationId: string,
        requestBody: TemplateUpdate,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/content/templates/{template_id}',
            path: {
                'template_id': templateId,
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
     * Delete a content template
     * @param templateId
     * @param organizationId
     * @returns void
     * @throws ApiError
     */
    public static deleteTemplateApiV1ContentTemplatesTemplateIdDelete(
        templateId: string,
        organizationId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/content/templates/{template_id}',
            path: {
                'template_id': templateId,
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
