/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type CreateProviderRequest = {
    organization_id: string;
    provider_type?: string;
    name: string;
    api_key: string;
    from_email: string;
    from_name?: string;
    config?: Record<string, any>;
};
