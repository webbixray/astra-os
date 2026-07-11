/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CreateJobRequest } from '../models/CreateJobRequest';
import type { LogActionRequest } from '../models/LogActionRequest';
import type { RecordApiCallRequest } from '../models/RecordApiCallRequest';
import type { UpdateJobStatusRequest } from '../models/UpdateJobStatusRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class MonitoringService {
    /**
     * Log audit action
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static logActionApiV1AuditLogsPost(
        organizationId: string,
        requestBody: LogActionRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/audit-logs',
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
     * Get audit logs
     * @param organizationId
     * @param action
     * @param resourceType
     * @param userId
     * @param page
     * @param limit
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getAuditLogsApiV1AuditLogsGet(
        organizationId: string,
        action?: (string | null),
        resourceType?: (string | null),
        userId?: (string | null),
        page: number = 1,
        limit: number = 50,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/audit-logs',
            query: {
                'organization_id': organizationId,
                'action': action,
                'resource_type': resourceType,
                'user_id': userId,
                'page': page,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get audit log summary
     * @param organizationId
     * @param hours
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getAuditSummaryApiV1AuditLogsSummaryGet(
        organizationId: string,
        hours: number = 24,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/audit-logs/summary',
            query: {
                'organization_id': organizationId,
                'hours': hours,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create background job
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createJobApiV1JobsPost(
        organizationId: string,
        requestBody: CreateJobRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/jobs',
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
     * List background jobs
     * @param organizationId
     * @param status
     * @param jobType
     * @param page
     * @param limit
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getJobsApiV1JobsGet(
        organizationId: string,
        status?: (string | null),
        jobType?: (string | null),
        page: number = 1,
        limit: number = 50,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/jobs',
            query: {
                'organization_id': organizationId,
                'status': status,
                'job_type': jobType,
                'page': page,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update job status
     * @param jobId
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateJobStatusApiV1JobsJobIdStatusPatch(
        jobId: string,
        organizationId: string,
        requestBody: UpdateJobStatusRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/jobs/{job_id}/status',
            path: {
                'job_id': jobId,
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
     * Retry failed job
     * @param jobId
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static retryJobApiV1JobsJobIdRetryPost(
        jobId: string,
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/jobs/{job_id}/retry',
            path: {
                'job_id': jobId,
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
     * Get job summary
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getJobSummaryApiV1JobsSummaryGet(
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/jobs/summary',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Record API usage
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static recordApiCallApiV1UsageRecordsPost(
        organizationId: string,
        requestBody: RecordApiCallRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/usage-records',
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
     * Get API usage records
     * @param organizationId
     * @param page
     * @param limit
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getUsageRecordsApiV1UsageRecordsGet(
        organizationId: string,
        page: number = 1,
        limit: number = 50,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/usage-records',
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
     * Get API usage stats
     * @param organizationId
     * @param hours
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getUsageStatsApiV1UsageRecordsStatsGet(
        organizationId: string,
        hours: number = 24,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/usage-records/stats',
            query: {
                'organization_id': organizationId,
                'hours': hours,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Check system health
     * @returns any Successful Response
     * @throws ApiError
     */
    public static checkSystemHealthApiV1SystemHealthGet(): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/system/health',
        });
    }
}
