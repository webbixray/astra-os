/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { app__presentation__routes__notifications__notification_hub_routes__CreateTemplateRequest } from '../models/app__presentation__routes__notifications__notification_hub_routes__CreateTemplateRequest';
import type { CreateAnnouncementRequest } from '../models/CreateAnnouncementRequest';
import type { PaginatedResponse } from '../models/PaginatedResponse';
import type { SendFromTemplateRequest } from '../models/SendFromTemplateRequest';
import type { SendNotificationRequest } from '../models/SendNotificationRequest';
import type { SetPreferenceRequest } from '../models/SetPreferenceRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class NotificationsService {
    /**
     * Stream notifications via SSE
     * @returns any Successful Response
     * @throws ApiError
     */
    public static streamNotificationsApiV1NotificationsStreamGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/notifications/stream',
        });
    }
    /**
     * List notifications
     * @param organizationId
     * @param unreadOnly
     * @param channel
     * @param archived
     * @param page
     * @param limit
     * @returns PaginatedResponse Successful Response
     * @throws ApiError
     */
    public static listNotificationsApiV1NotificationsGet(
        organizationId: string,
        unreadOnly: boolean = false,
        channel?: (string | null),
        archived: boolean = false,
        page: number = 1,
        limit: number = 50,
    ): CancelablePromise<PaginatedResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/notifications',
            query: {
                'organization_id': organizationId,
                'unread_only': unreadOnly,
                'channel': channel,
                'archived': archived,
                'page': page,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get unread notification count
     * @param organizationId
     * @param channel
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getUnreadCountApiV1NotificationsUnreadCountGet(
        organizationId: string,
        channel?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/notifications/unread-count',
            query: {
                'organization_id': organizationId,
                'channel': channel,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Mark notification as read
     * @param notificationId
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static markNotificationReadApiV1NotificationsNotificationIdReadPatch(
        notificationId: string,
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/notifications/{notification_id}/read',
            path: {
                'notification_id': notificationId,
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
     * Mark all notifications as read
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static markAllNotificationsReadApiV1NotificationsReadAllPost(
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/notifications/read-all',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Archive notification
     * @param notificationId
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static archiveNotificationApiV1NotificationsNotificationIdArchivePatch(
        notificationId: string,
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/notifications/{notification_id}/archive',
            path: {
                'notification_id': notificationId,
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
     * Search notifications
     * @param organizationId
     * @param q
     * @param limit
     * @param offset
     * @returns any Successful Response
     * @throws ApiError
     */
    public static searchNotificationsApiV1NotificationsSearchGet(
        organizationId: string,
        q: string,
        limit: number = 50,
        offset?: number,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/notifications/search',
            query: {
                'organization_id': organizationId,
                'q': q,
                'limit': limit,
                'offset': offset,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Send notification
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static sendNotificationApiV1NotificationsSendPost(
        requestBody: SendNotificationRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/notifications/send',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Send notification from template
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static sendFromTemplateApiV1NotificationsSendFromTemplatePost(
        requestBody: SendFromTemplateRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/notifications/send-from-template',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create notification template
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createTemplateApiV1NotificationTemplatesPost(
        organizationId: string,
        requestBody: app__presentation__routes__notifications__notification_hub_routes__CreateTemplateRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/notification-templates',
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
     * List notification templates
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listTemplatesApiV1NotificationTemplatesGet(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/notification-templates',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get notification template
     * @param templateId
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getTemplateApiV1NotificationTemplatesTemplateIdGet(
        templateId: string,
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/notification-templates/{template_id}',
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
     * Delete notification template
     * @param templateId
     * @param organizationId
     * @returns void
     * @throws ApiError
     */
    public static deleteTemplateApiV1NotificationTemplatesTemplateIdDelete(
        templateId: string,
        organizationId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/notification-templates/{template_id}',
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
     * Get notification preferences
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getPreferencesApiV1NotificationPreferencesGet(): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/notification-preferences',
        });
    }
    /**
     * Set notification preference
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static setPreferenceApiV1NotificationPreferencesPut(
        requestBody: SetPreferenceRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/notification-preferences',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create announcement
     * @param organizationId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createAnnouncementApiV1AnnouncementsPost(
        organizationId: string,
        requestBody: CreateAnnouncementRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/announcements',
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
     * List announcements
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listAnnouncementsApiV1AnnouncementsGet(
        organizationId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/announcements',
            query: {
                'organization_id': organizationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Dismiss announcement
     * @param announcementId
     * @param organizationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static dismissAnnouncementApiV1AnnouncementsAnnouncementIdDismissPost(
        announcementId: string,
        organizationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/announcements/{announcement_id}/dismiss',
            path: {
                'announcement_id': announcementId,
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
     * Delete announcement
     * @param announcementId
     * @param organizationId
     * @returns void
     * @throws ApiError
     */
    public static deleteAnnouncementApiV1AnnouncementsAnnouncementIdDelete(
        announcementId: string,
        organizationId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/announcements/{announcement_id}',
            path: {
                'announcement_id': announcementId,
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
