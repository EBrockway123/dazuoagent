/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BoardType } from '../models/BoardType';
import type { HardwareCategory } from '../models/HardwareCategory';
import type { MaterialCreate } from '../models/MaterialCreate';
import type { MaterialListResponse } from '../models/MaterialListResponse';
import type { MaterialRead } from '../models/MaterialRead';
import type { Veneer } from '../models/Veneer';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class MaterialsService {
    /**
     * 列出素材(可筛选)
     * 按板材类型 / 贴皮 / 五金类型 / 关键词筛选素材库。
     * @param boardType 按板材基材筛选:颗粒板 / 多层板 / 密度板 / 实木
     * @param veneer 按表面工艺筛选:三聚氰胺 / 烤漆 / PVC 贴膜 / 实木贴皮 / 包覆
     * @param hardwareCategory 按五金类型筛选:铰链 / 滑轨 / 拉手 / 气撑 / 挂衣杆
     * @param keyword 对 SKU / 名称做模糊匹配,例如输入 '白色' 或 '橡木'。
     * @param skip 分页起始位置
     * @param limit 每页最大条数,默认 50,最大 200
     * @returns MaterialListResponse Successful Response
     * @throws ApiError
     */
    public static listMaterialsApiV1MaterialsGet(
        boardType?: (BoardType | null),
        veneer?: (Veneer | null),
        hardwareCategory?: (HardwareCategory | null),
        keyword?: (string | null),
        skip?: number,
        limit: number = 50,
    ): CancelablePromise<MaterialListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/materials',
            query: {
                'board_type': boardType,
                'veneer': veneer,
                'hardware_category': hardwareCategory,
                'keyword': keyword,
                'skip': skip,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 新建素材
     * 手动录入新素材。生产环境应限制为管理员调用(后续接权限层)。
     * @param requestBody
     * @returns MaterialRead Successful Response
     * @throws ApiError
     */
    public static createMaterialApiV1MaterialsPost(
        requestBody: MaterialCreate,
    ): CancelablePromise<MaterialRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/materials',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 查单个素材
     * 按 id 查一条素材的完整记录。
     * @param materialId
     * @returns MaterialRead Successful Response
     * @throws ApiError
     */
    public static getMaterialApiV1MaterialsMaterialIdGet(
        materialId: number,
    ): CancelablePromise<MaterialRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/materials/{material_id}',
            path: {
                'material_id': materialId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
