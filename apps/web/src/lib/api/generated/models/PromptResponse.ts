/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
 
export type PromptResponse = {
    id: string;
    org_id?: (string | null);
    name: string;
    description: string;
    category: string;
    content: string;
    variables: Array<string>;
    version: number;
    status: string;
    is_builtin: boolean;
    created_by?: (string | null);
    created_at: string;
    updated_at: string;
};

