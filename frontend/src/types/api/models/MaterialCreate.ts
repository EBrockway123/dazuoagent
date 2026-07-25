/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BoardType } from './BoardType';
import type { HardwareCategory } from './HardwareCategory';
import type { Veneer } from './Veneer';
export type MaterialCreate = {
    sku: string;
    name: string;
    board_type?: (BoardType | null);
    thickness_mm?: (number | null);
    veneer?: (Veneer | null);
    hardware_category?: (HardwareCategory | null);
    color_code?: (string | null);
    image_url?: (string | null);
    supplier?: (string | null);
    price: number;
    unit?: string;
};

