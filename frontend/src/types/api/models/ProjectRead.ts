/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DesignRead } from './DesignRead';
import type { RoomRead } from './RoomRead';
export type ProjectRead = {
    name: string;
    customer_name: string;
    customer_phone?: (string | null);
    address?: (string | null);
    floor_plan_file?: (string | null);
    floor_plan_layout?: (string | null);
    id: number;
    rooms?: Array<RoomRead>;
    designs?: Array<DesignRead>;
    created_at: string;
    updated_at: string;
};

