/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FurnitureRead } from './FurnitureRead';
export type DesignRead = {
    name: string;
    summary?: (string | null);
    is_final?: boolean;
    id: number;
    project_id: number;
    furniture?: Array<FurnitureRead>;
    created_at: string;
    updated_at: string;
};

