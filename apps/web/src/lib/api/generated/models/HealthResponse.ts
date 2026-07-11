/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type HealthResponse = {
    status: string;
    version: string;
    timestamp: string;
    checks?: (Record<string, boolean> | null);
    details?: (Record<string, string> | null);
    duration_ms?: (string | null);
};

