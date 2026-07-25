/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_parse_floorplan_api_v1_agents_projects__project_id__parse_floorplan_post } from '../models/Body_parse_floorplan_api_v1_agents_projects__project_id__parse_floorplan_post';
import type { ChatRequest } from '../models/ChatRequest';
import type { ChatResponse } from '../models/ChatResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AiAgentsService {
    /**
     * 与设计助理对话(一轮)
     * 无状态接口:前端保存历史,每次发完整消息列表。如带上 `project_id`,智能体可以调用项目级工具(查房间清单等)。
     * @param requestBody
     * @returns ChatResponse Successful Response
     * @throws ApiError
     */
    public static chatApiV1AgentsChatPost(
        requestBody: ChatRequest,
    ): CancelablePromise<ChatResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/agents/chat',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 上传平面图并解析房间
     * 上传一张 JPG/PNG/PDF 格式的房屋平面图,后台调用视觉模型或 OCR 解析。 返回建议的房间清单(主卧 / 客厅 / 厨房 …)。 客户端确认后,再通过 `POST /projects` 写入。
     * @param projectId
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static parseFloorplanApiV1AgentsProjectsProjectIdParseFloorplanPost(
        projectId: number,
        formData: Body_parse_floorplan_api_v1_agents_projects__project_id__parse_floorplan_post,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/agents/projects/{project_id}/parse-floorplan',
            path: {
                'project_id': projectId,
            },
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
