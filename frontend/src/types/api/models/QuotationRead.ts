/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { QuotationLineItemRead } from './QuotationLineItemRead';
import type { QuotationStatus } from './QuotationStatus';
export type QuotationRead = {
    project_id: number;
    design_id?: (number | null);
    status?: QuotationStatus;
    labor_cost?: number;
    tax?: number;
    notes?: (string | null);
    id: number;
    subtotal: number;
    total: number;
    line_items?: Array<QuotationLineItemRead>;
    created_at: string;
    updated_at: string;
};

