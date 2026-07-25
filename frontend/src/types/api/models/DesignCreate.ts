/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FurnitureCreate } from './FurnitureCreate';
export type DesignCreate = {
    name: string;
    summary?: (string | null);
    is_final?: boolean;
    project_id: number;
    furniture?: Array<FurnitureCreate>;
};

