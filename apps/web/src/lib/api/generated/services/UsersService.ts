/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CreateUserRequest } from '../models/CreateUserRequest';
import type { UpdateUserRequest } from '../models/UpdateUserRequest';
import type { UserResponse } from '../models/UserResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class UsersService {
    /**
     * Create a new user
     * @param requestBody
     * @returns UserResponse Successful Response
     * @throws ApiError
     */
    public static createUserApiV1UsersPost(
        requestBody: CreateUserRequest,
    ): CancelablePromise<UserResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/users',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get user by ID
     * @param userId
     * @returns UserResponse Successful Response
     * @throws ApiError
     */
    public static getUserApiV1UsersUserIdGet(
        userId: string,
    ): CancelablePromise<UserResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/users/{user_id}',
            path: {
                'user_id': userId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update user profile
     * @param userId
     * @param requestBody
     * @returns UserResponse Successful Response
     * @throws ApiError
     */
    public static updateUserApiV1UsersUserIdPatch(
        userId: string,
        requestBody: UpdateUserRequest,
    ): CancelablePromise<UserResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/users/{user_id}',
            path: {
                'user_id': userId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
