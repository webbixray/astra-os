/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChatMessageSchema } from './ChatMessageSchema';
export type ChatRequestSchema = {
    organization_id: string;
    message: string;
    conversation_id?: (string | null);
    page_context?: (Record<string, any> | null);
    messages?: (Array<ChatMessageSchema> | null);
};

