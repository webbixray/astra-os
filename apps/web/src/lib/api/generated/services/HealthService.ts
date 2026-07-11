/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { HealthResponse } from '../models/HealthResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class HealthService {
    /**
     * Check application health
     * @returns HealthResponse Successful Response
     * @throws ApiError
     */
    public static healthCheckApiV1HealthGet(): CancelablePromise<HealthResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/health',
        });
    }
    /**
     * Check liveness
     * @returns string Successful Response
     * @throws ApiError
     */
    public static livenessApiV1HealthLiveGet(): CancelablePromise<Record<string, string>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/health/live',
        });
    }
    /**
     * Check readiness
     * @returns any Successful Response
     * @throws ApiError
     */
    public static readinessApiV1HealthReadyGet(): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/health/ready',
        });
    }
    /**
     * Get API root info
     * @returns string Successful Response
     * @throws ApiError
     */
    public static rootApiV1Get(): CancelablePromise<Record<string, string>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/',
        });
    }
}
