/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DesignCreate } from '../models/DesignCreate';
import type { DesignRead } from '../models/DesignRead';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DesignsService {
    /**
     * 保存设计方案草稿
     * 为某个项目创建一个新的设计方案,内含家具清单(尺寸 / 材质 / 房间归属)。 `is_final=true` 之后该方案可以用于生成报价单。
     * @param requestBody
     * @returns DesignRead Successful Response
     * @throws ApiError
     */
    public static createDesignApiV1DesignsPost(
        requestBody: DesignCreate,
    ): CancelablePromise<DesignRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/designs',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 查单个设计方案
     * 按 id 拉一个设计方案的完整内容(含家具列表)。
     * @param designId
     * @returns DesignRead Successful Response
     * @throws ApiError
     */
    public static getDesignApiV1DesignsDesignIdGet(
        designId: number,
    ): CancelablePromise<DesignRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/designs/{design_id}',
            path: {
                'design_id': designId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
