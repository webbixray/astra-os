/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { app__presentation__routes__reports__report_routes_v2__CreateTemplateRequest } from '../models/app__presentation__routes__reports__report_routes_v2__CreateTemplateRequest';
import type { ComparePeriodsRequest } from '../models/ComparePeriodsRequest';
import type { CreateScheduleRequest } from '../models/CreateScheduleRequest';
import type { DeliverReportRequest } from '../models/DeliverReportRequest';
import type { UpdateScheduleRequest } from '../models/UpdateScheduleRequest';
import type { UpdateTemplateRequest } from '../models/UpdateTemplateRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ReportsService {
    /**
     * Get report overview
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getReportOverviewApiV1ReportsOverviewGet(
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/reports/overview',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get campaign report
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getReportCampaignsApiV1ReportsCampaignsGet(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/reports/campaigns',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get ad performance report
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getReportAdsApiV1ReportsAdsGet(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/reports/ads',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get metric trends
     * @param organizationId
     * @param metric
     * @param days
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getReportTrendsApiV1ReportsTrendsGet(
        organizationId: string,
        metric: string = 'spend',
        days: number = 30,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/reports/trends',
            query: {
                'organization_id': organizationId,
                'metric': metric,
                'days': days,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get campaign timeline
     * @param organizationId
     * @param campaignIds
     * @param startDate
     * @param endDate
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getCampaignTimelineApiV1ReportsCampaignsTimelineGet(
        organizationId: string,
        campaignIds: string,
        startDate: string,
        endDate: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/reports/campaigns/timeline',
            query: {
                'organization_id': organizationId,
                'campaign_ids': campaignIds,
                'start_date': startDate,
                'end_date': endDate,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get platform comparison
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getPlatformComparisonApiV1ReportsPlatformsGet(
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/reports/platforms',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Export report as CSV
     * @param type
     * @param organizationId
     * @param startDate
     * @param endDate
     * @returns any Successful Response
     * @throws ApiError
     */
    public static exportReportCsvApiV1ReportsExportCsvGet(
        type: string,
        organizationId: string,
        startDate?: (string | null),
        endDate?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/reports/export/csv',
            query: {
                'type': type,
                'organization_id': organizationId,
                'start_date': startDate,
                'end_date': endDate,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create report schedule
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createReportScheduleApiV1ReportsSchedulesPost(
        requestBody: CreateScheduleRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/reports/schedules',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List report schedules
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listReportSchedulesApiV1ReportsSchedulesGet(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/reports/schedules',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update report schedule
     * @param scheduleId
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateReportScheduleApiV1ReportsSchedulesScheduleIdPatch(
        scheduleId: string,
        organizationId: string,
        requestBody: UpdateScheduleRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/reports/schedules/{schedule_id}',
            path: {
                'schedule_id': scheduleId,
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
     * Delete report schedule
     * @param scheduleId
     * @param organizationId
     * @returns void
     * @throws ApiError
     */
    public static deleteReportScheduleApiV1ReportsSchedulesScheduleIdDelete(
        scheduleId: string,
        organizationId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/reports/schedules/{schedule_id}',
            path: {
                'schedule_id': scheduleId,
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
     * Create report template
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createTemplateApiV1ReportsTemplatesPost(
        organizationId: string,
        requestBody: app__presentation__routes__reports__report_routes_v2__CreateTemplateRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/reports/templates',
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
     * List report templates
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listTemplatesApiV1ReportsTemplatesGet(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/reports/templates',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get report template
     * @param templateId
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getTemplateApiV1ReportsTemplatesTemplateIdGet(
        templateId: string,
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/reports/templates/{template_id}',
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
     * Update report template
     * @param templateId
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateTemplateApiV1ReportsTemplatesTemplateIdPut(
        templateId: string,
        organizationId: string,
        requestBody: UpdateTemplateRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/reports/templates/{template_id}',
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
     * Delete report template
     * @param templateId
     * @param organizationId
     * @returns void
     * @throws ApiError
     */
    public static deleteTemplateApiV1ReportsTemplatesTemplateIdDelete(
        templateId: string,
        organizationId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/reports/templates/{template_id}',
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
     * Generate report
     * @param reportType
     * @param organizationId
     * @param format
     * @param days
     * @returns any Successful Response
     * @throws ApiError
     */
    public static generateReportApiV1ReportsGenerateReportTypeGet(
        reportType: string,
        organizationId: string,
        format: string = 'csv',
        days: number = 30,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/reports/generate/{report_type}',
            path: {
                'report_type': reportType,
            },
            query: {
                'organization_id': organizationId,
                'format': format,
                'days': days,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Deliver report
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deliverReportApiV1ReportsDeliverPost(
        organizationId: string,
        requestBody: DeliverReportRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/reports/deliver',
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
     * Get delivery logs
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getDeliveryLogsApiV1ReportsDeliveryLogsGet(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/reports/delivery-logs',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Compare reporting periods
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static comparePeriodsApiV1ReportsComparePost(
        organizationId: string,
        requestBody: ComparePeriodsRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/reports/compare',
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
}
