/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AddPermissionRequest } from '../models/AddPermissionRequest';
import type { ChangePlanRequest } from '../models/ChangePlanRequest';
import type { ChangeRoleRequest } from '../models/ChangeRoleRequest';
import type { CreateOrganizationRequest } from '../models/CreateOrganizationRequest';
import type { CreateSubOrgRequest } from '../models/CreateSubOrgRequest';
import type { InviteMemberRequest } from '../models/InviteMemberRequest';
import type { OrganizationResponse } from '../models/OrganizationResponse';
import type { PaginatedResponse_OrganizationResponse_ } from '../models/PaginatedResponse_OrganizationResponse_';
import type { SetFeatureFlagRequest } from '../models/SetFeatureFlagRequest';
import type { SetParentRequest } from '../models/SetParentRequest';
import type { UpdateOrganizationRequest } from '../models/UpdateOrganizationRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class OrganizationsService {
    /**
     * Create organization
     * @param requestBody
     * @returns OrganizationResponse Successful Response
     * @throws ApiError
     */
    public static createOrganizationApiV1OrganizationsPost(
        requestBody: CreateOrganizationRequest,
    ): CancelablePromise<OrganizationResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/organizations',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List user organizations
     * @param page
     * @param limit
     * @returns PaginatedResponse_OrganizationResponse_ Successful Response
     * @throws ApiError
     */
    public static listMyOrganizationsApiV1OrganizationsMyGet(
        page: number = 1,
        limit: number = 50,
    ): CancelablePromise<PaginatedResponse_OrganizationResponse_> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/organizations/my',
            query: {
                'page': page,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get organization details
     * @param orgId
     * @returns OrganizationResponse Successful Response
     * @throws ApiError
     */
    public static getOrganizationApiV1OrganizationsOrgIdGet(
        orgId: string,
    ): CancelablePromise<OrganizationResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/organizations/{org_id}',
            path: {
                'org_id': orgId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update organization
     * @param orgId
     * @param requestBody
     * @returns OrganizationResponse Successful Response
     * @throws ApiError
     */
    public static updateOrganizationApiV1OrganizationsOrgIdPatch(
        orgId: string,
        requestBody: UpdateOrganizationRequest,
    ): CancelablePromise<OrganizationResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/organizations/{org_id}',
            path: {
                'org_id': orgId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get organization tree
     * @param orgId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getOrgTreeApiV1OrganizationsOrgIdTreeGet(
        orgId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/organizations/{org_id}/tree',
            path: {
                'org_id': orgId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Set parent organization
     * @param orgId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static setParentOrgApiV1OrganizationsOrgIdParentPost(
        orgId: string,
        requestBody: SetParentRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/organizations/{org_id}/parent',
            path: {
                'org_id': orgId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create sub-organization
     * @param orgId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createSubOrgApiV1OrganizationsOrgIdSubOrgsPost(
        orgId: string,
        requestBody: CreateSubOrgRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/organizations/{org_id}/sub-orgs',
            path: {
                'org_id': orgId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Invite member to organization
     * @param orgId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static inviteMemberApiV1OrganizationsOrgIdInvitationsPost(
        orgId: string,
        requestBody: InviteMemberRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/organizations/{org_id}/invitations',
            path: {
                'org_id': orgId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List organization invitations
     * @param orgId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listInvitationsApiV1OrganizationsOrgIdInvitationsGet(
        orgId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/organizations/{org_id}/invitations',
            path: {
                'org_id': orgId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Accept invitation
     * @param invitationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static acceptInvitationApiV1InvitationsInvitationIdAcceptPost(
        invitationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/invitations/{invitation_id}/accept',
            path: {
                'invitation_id': invitationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Reject invitation
     * @param invitationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static rejectInvitationApiV1InvitationsInvitationIdRejectPost(
        invitationId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/invitations/{invitation_id}/reject',
            path: {
                'invitation_id': invitationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Cancel invitation
     * @param orgId
     * @param invitationId
     * @returns void
     * @throws ApiError
     */
    public static cancelInvitationApiV1OrganizationsOrgIdInvitationsInvitationIdDelete(
        orgId: string,
        invitationId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/organizations/{org_id}/invitations/{invitation_id}',
            path: {
                'org_id': orgId,
                'invitation_id': invitationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List organization members
     * @param orgId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listMembersApiV1OrganizationsOrgIdMembersGet(
        orgId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/organizations/{org_id}/members',
            path: {
                'org_id': orgId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Change member role
     * @param orgId
     * @param memberId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static changeMemberRoleApiV1OrganizationsOrgIdMembersMemberIdRolePatch(
        orgId: string,
        memberId: string,
        requestBody: ChangeRoleRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/organizations/{org_id}/members/{member_id}/role',
            path: {
                'org_id': orgId,
                'member_id': memberId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Remove member
     * @param orgId
     * @param memberId
     * @returns void
     * @throws ApiError
     */
    public static removeMemberApiV1OrganizationsOrgIdMembersMemberIdDelete(
        orgId: string,
        memberId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/organizations/{org_id}/members/{member_id}',
            path: {
                'org_id': orgId,
                'member_id': memberId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List feature flags
     * @param orgId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listFeatureFlagsApiV1OrganizationsOrgIdFeaturesGet(
        orgId: string,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/organizations/{org_id}/features',
            path: {
                'org_id': orgId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Set feature flag
     * @param orgId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static setFeatureFlagApiV1OrganizationsOrgIdFeaturesPut(
        orgId: string,
        requestBody: SetFeatureFlagRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/organizations/{org_id}/features',
            path: {
                'org_id': orgId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete feature flag
     * @param orgId
     * @param flagId
     * @returns void
     * @throws ApiError
     */
    public static deleteFeatureFlagApiV1OrganizationsOrgIdFeaturesFlagIdDelete(
        orgId: string,
        flagId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/organizations/{org_id}/features/{flag_id}',
            path: {
                'org_id': orgId,
                'flag_id': flagId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get usage summary
     * @param orgId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getUsageApiV1OrganizationsOrgIdUsageGet(
        orgId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/organizations/{org_id}/usage',
            path: {
                'org_id': orgId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get usage trend
     * @param orgId
     * @param metric
     * @param days
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getUsageTrendApiV1OrganizationsOrgIdUsageMetricTrendGet(
        orgId: string,
        metric: string,
        days: number = 30,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/organizations/{org_id}/usage/{metric}/trend',
            path: {
                'org_id': orgId,
                'metric': metric,
            },
            query: {
                'days': days,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get billing plan
     * @param orgId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getBillingPlanApiV1OrganizationsOrgIdBillingGet(
        orgId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/organizations/{org_id}/billing',
            path: {
                'org_id': orgId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Change billing plan
     * @param orgId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static changeBillingPlanApiV1OrganizationsOrgIdBillingPut(
        orgId: string,
        requestBody: ChangePlanRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/organizations/{org_id}/billing',
            path: {
                'org_id': orgId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Check permission
     * @param orgId
     * @param permission
     * @returns any Successful Response
     * @throws ApiError
     */
    public static checkPermissionApiV1OrganizationsOrgIdCheckPermissionPermissionGet(
        orgId: string,
        permission: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/organizations/{org_id}/check-permission/{permission}',
            path: {
                'org_id': orgId,
                'permission': permission,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Add member permission
     * @param orgId
     * @param memberId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static addMemberPermissionApiV1OrganizationsOrgIdMembersMemberIdPermissionsPost(
        orgId: string,
        memberId: string,
        requestBody: AddPermissionRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/organizations/{org_id}/members/{member_id}/permissions',
            path: {
                'org_id': orgId,
                'member_id': memberId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Remove member permission
     * @param orgId
     * @param memberId
     * @param permission
     * @returns any Successful Response
     * @throws ApiError
     */
    public static removeMemberPermissionApiV1OrganizationsOrgIdMembersMemberIdPermissionsPermissionDelete(
        orgId: string,
        memberId: string,
        permission: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/organizations/{org_id}/members/{member_id}/permissions/{permission}',
            path: {
                'org_id': orgId,
                'member_id': memberId,
                'permission': permission,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
