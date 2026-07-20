/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */

export type BulkGenerateRequest = {
    organization_id: string;
    template_id: string;
    variable_rows: Array<Record<string, string>>;
    brand_voice_id?: (string | null);
    tone?: (string | null);
};
