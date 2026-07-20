/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */

export type app__presentation__routes__campaigns__campaign_routes__CreateCampaignRequest = {
    name: string;
    description?: (string | null);
    budget_amount?: (number | null);
    budget_currency?: string;
    start_date?: (string | null);
    end_date?: (string | null);
    channels?: Array<string>;
    objective?: (string | null);
    organization_id: string;
};
