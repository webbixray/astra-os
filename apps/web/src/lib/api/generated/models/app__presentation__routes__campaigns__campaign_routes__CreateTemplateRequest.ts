/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type app__presentation__routes__campaigns__campaign_routes__CreateTemplateRequest = {
    name: string;
    description?: string;
    channels?: Array<string>;
    objective?: (string | null);
    budget_amount?: (number | null);
    budget_currency?: string;
    default_duration_days?: number;
    config?: Record<string, any>;
    organization_id: string;
};

