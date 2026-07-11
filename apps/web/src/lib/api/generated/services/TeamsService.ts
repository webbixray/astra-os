/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { InviteRequest } from '../models/InviteRequest';
import type { PaginatedResponse_MemberResponse_ } from '../models/PaginatedResponse_MemberResponse_';
import type { UpdateMemberRoleRequest } from '../models/UpdateMemberRoleRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class TeamsService {
    /**
     * Invite Member
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static inviteMemberApiV1TeamsInvitePost(
        requestBody: InviteRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/teams/invite',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Members
     * @param organizationId
     * @param page
     * @param limit
     * @returns PaginatedResponse_MemberResponse_ Successful Response
     * @throws ApiError
     */
    public static listMembersApiV1TeamsMembersGet(
        organizationId: string,
        page: number = 1,
        limit: number = 50,
    ): CancelablePromise<PaginatedResponse_MemberResponse_> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/teams/members',
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
     * Update Member Role
     * @param memberId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateMemberRoleApiV1TeamsMembersMemberIdRolePatch(
        memberId: string,
        requestBody: UpdateMemberRoleRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/teams/members/{member_id}/role',
            path: {
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
     * Remove Member
     * @param memberId
     * @returns void
     * @throws ApiError
     */
    public static removeMemberApiV1TeamsMembersMemberIdDelete(
        memberId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/teams/members/{member_id}',
            path: {
                'member_id': memberId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
