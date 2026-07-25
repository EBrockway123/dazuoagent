/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { QuotationCreate } from '../models/QuotationCreate';
import type { QuotationRead } from '../models/QuotationRead';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class QuotationsService {
    /**
     * 新建报价单
     * 创建一个空报价单,行项由后续调用 `generate-from-design` 接口根据设计方案自动计算并填入。 也可以手工传 `line_items` 直接给(例如客户选定某些促销套餐)。
     * @param requestBody
     * @returns QuotationRead Successful Response
     * @throws ApiError
     */
    public static createQuotationApiV1QuotationsPost(
        requestBody: QuotationCreate,
    ): CancelablePromise<QuotationRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/quotations',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 查报价单
     * 按 id 拉一条报价单,含所有行项明细和小计 / 人工 / 合计。
     * @param quotationId
     * @returns QuotationRead Successful Response
     * @throws ApiError
     */
    public static getQuotationApiV1QuotationsQuotationIdGet(
        quotationId: number,
    ): CancelablePromise<QuotationRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/quotations/{quotation_id}',
            path: {
                'quotation_id': quotationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 基于设计算价
     * 调用报价引擎(`quotation_service.recompute_from_design`),根据 `design_id` 中的家具清单自动拆板 → 算每件行项明细 → 重算小计 / 人工 / 合计。 会清空既有行项重新生成。
     * @param quotationId
     * @param designId
     * @returns QuotationRead Successful Response
     * @throws ApiError
     */
    public static generateFromDesignApiV1QuotationsQuotationIdGenerateFromDesignDesignIdPost(
        quotationId: number,
        designId: number,
    ): CancelablePromise<QuotationRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/quotations/{quotation_id}/generate-from-design/{design_id}',
            path: {
                'quotation_id': quotationId,
                'design_id': designId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
