/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AuthResponse } from '../models/AuthResponse';
import type { MessageResponse } from '../models/MessageResponse';
import type { RefreshRequest } from '../models/RefreshRequest';
import type { SignInRequest } from '../models/SignInRequest';
import type { SignUpRequest } from '../models/SignUpRequest';
import type { UserResponse } from '../models/UserResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AuthService {
    /**
     * Register a new user
     * @param requestBody
     * @returns AuthResponse Successful Response
     * @throws ApiError
     */
    public static signUpApiV1AuthSignupPost(
        requestBody: SignUpRequest,
    ): CancelablePromise<AuthResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/auth/signup',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Sign in with credentials
     * @param requestBody
     * @returns AuthResponse Successful Response
     * @throws ApiError
     */
    public static signInApiV1AuthSigninPost(
        requestBody: SignInRequest,
    ): CancelablePromise<AuthResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/auth/signin',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Refresh access token
     * @param requestBody
     * @returns AuthResponse Successful Response
     * @throws ApiError
     */
    public static refreshTokenApiV1AuthRefreshPost(
        requestBody: RefreshRequest,
    ): CancelablePromise<AuthResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/auth/refresh',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Log out user
     * @param requestBody
     * @returns MessageResponse Successful Response
     * @throws ApiError
     */
    public static logoutApiV1AuthLogoutPost(
        requestBody: RefreshRequest,
    ): CancelablePromise<MessageResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/auth/logout',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get current user profile
     * @returns UserResponse Successful Response
     * @throws ApiError
     */
    public static getCurrentUserApiV1AuthMeGet(): CancelablePromise<UserResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/auth/me',
        });
    }
}
