/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class MetricsService {
    /**
     * Prometheus metrics (public)
     * Public Prometheus metrics endpoint - no authentication required.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static metricsApiV1MetricsGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/metrics',
        });
    }
    /**
     * Business metrics (authenticated)
     * @returns number Successful Response
     * @throws ApiError
     */
    public static businessMetricsApiV1MetricsBusinessGet(): CancelablePromise<Record<string, number>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/metrics/business',
        });
    }
}
