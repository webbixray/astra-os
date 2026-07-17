/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
 
export type CampaignResponse = {
    id: string;
    organization_id: string;
    name: string;
    description?: (string | null);
    status: string;
    budget_amount?: (number | null);
    budget_currency?: string;
    start_date?: (string | null);
    end_date?: (string | null);
    channels?: Array<string>;
    objective?: (string | null);
    created_by: string;
    ai_generated?: boolean;
    created_at: string;
    updated_at: string;
};

