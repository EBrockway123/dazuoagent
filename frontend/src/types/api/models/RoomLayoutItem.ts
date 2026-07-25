/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * One room's position + rotation on the 2D floor plan canvas (mm).
 */
export type RoomLayoutItem = {
    room_id: number;
    /**
     * 房间左下角 X 坐标 (mm)
     */
    x_mm: number;
    /**
     * 房间左下角 Y 坐标 (mm)
     */
    y_mm: number;
    /**
     * 顺时针旋转角度
     */
    rotation_deg?: number;
};

