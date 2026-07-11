/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CreateDashboardRequest } from '../models/CreateDashboardRequest';
import type { CreateWidgetRequest } from '../models/CreateWidgetRequest';
import type { UpdateWidgetRequest } from '../models/UpdateWidgetRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DashboardsService {
    /**
     * Create a new dashboard
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createDashboardApiV1DashboardsPost(
        requestBody: CreateDashboardRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/dashboards',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List all dashboards
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listDashboardsApiV1DashboardsGet(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/dashboards',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get dashboard by ID
     * @param dashboardId
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getDashboardApiV1DashboardsDashboardIdGet(
        dashboardId: string,
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/dashboards/{dashboard_id}',
            path: {
                'dashboard_id': dashboardId,
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
     * Delete a dashboard
     * @param dashboardId
     * @param organizationId
     * @returns void
     * @throws ApiError
     */
    public static deleteDashboardApiV1DashboardsDashboardIdDelete(
        dashboardId: string,
        organizationId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/dashboards/{dashboard_id}',
            path: {
                'dashboard_id': dashboardId,
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
     * Add widget to dashboard
     * @param dashboardId
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static addWidgetApiV1DashboardsDashboardIdWidgetsPost(
        dashboardId: string,
        organizationId: string,
        requestBody: CreateWidgetRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/dashboards/{dashboard_id}/widgets',
            path: {
                'dashboard_id': dashboardId,
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
     * Update a widget
     * @param widgetId
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateWidgetApiV1DashboardsWidgetsWidgetIdPut(
        widgetId: string,
        organizationId: string,
        requestBody: UpdateWidgetRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/dashboards/widgets/{widget_id}',
            path: {
                'widget_id': widgetId,
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
     * Delete a widget
     * @param widgetId
     * @param organizationId
     * @returns void
     * @throws ApiError
     */
    public static deleteWidgetApiV1DashboardsWidgetsWidgetIdDelete(
        widgetId: string,
        organizationId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/dashboards/widgets/{widget_id}',
            path: {
                'widget_id': widgetId,
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
     * Get dashboard data
     * @param dashboardId
     * @param organizationId
     * @param days
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getDashboardDataApiV1DashboardsDashboardIdDataGet(
        dashboardId: string,
        organizationId: string,
        days: number = 30,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/dashboards/{dashboard_id}/data',
            path: {
                'dashboard_id': dashboardId,
            },
            query: {
                'organization_id': organizationId,
                'days': days,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get a single metric
     * @param metric
     * @param organizationId
     * @param days
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getMetricApiV1DashboardsMetricsMetricGet(
        metric: string,
        organizationId: string,
        days: number = 30,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/dashboards/metrics/{metric}',
            path: {
                'metric': metric,
            },
            query: {
                'organization_id': organizationId,
                'days': days,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get metric anomalies
     * @param metric
     * @param organizationId
     * @param days
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getAnomaliesApiV1DashboardsAnomaliesMetricGet(
        metric: string,
        organizationId: string,
        days: number = 90,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/dashboards/anomalies/{metric}',
            path: {
                'metric': metric,
            },
            query: {
                'organization_id': organizationId,
                'days': days,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get metric predictions
     * @param metric
     * @param organizationId
     * @param periods
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getPredictionsApiV1DashboardsPredictionsMetricGet(
        metric: string,
        organizationId: string,
        periods: number = 7,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/dashboards/predictions/{metric}',
            path: {
                'metric': metric,
            },
            query: {
                'organization_id': organizationId,
                'periods': periods,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
