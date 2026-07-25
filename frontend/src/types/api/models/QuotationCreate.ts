/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { QuotationLineItemCreate } from './QuotationLineItemCreate';
import type { QuotationStatus } from './QuotationStatus';
export type QuotationCreate = {
    project_id: number;
    design_id?: (number | null);
    status?: QuotationStatus;
    labor_cost?: number;
    tax?: number;
    notes?: (string | null);
    line_items?: Array<QuotationLineItemCreate>;
};

