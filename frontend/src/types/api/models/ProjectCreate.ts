/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RoomCreate } from './RoomCreate';
export type ProjectCreate = {
    name: string;
    customer_name: string;
    customer_phone?: (string | null);
    address?: (string | null);
    floor_plan_file?: (string | null);
    floor_plan_layout?: (string | null);
    rooms?: Array<RoomCreate>;
};

