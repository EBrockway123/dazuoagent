/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FurnitureType } from './FurnitureType';
export type FurnitureCreate = {
    type: FurnitureType;
    label: string;
    width_mm: number;
    height_mm: number;
    depth_mm: number;
    material_id?: (number | null);
    room_id?: (number | null);
};

