/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type CreateScheduleRequest = {
    organization_id: string;
    name: string;
    report_type?: string;
    frequency?: string;
    recipients?: Array<string>;
    config?: Record<string, any>;
};
