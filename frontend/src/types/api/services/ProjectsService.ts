/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProjectCreate } from '../models/ProjectCreate';
import type { ProjectLayoutResponse } from '../models/ProjectLayoutResponse';
import type { ProjectLayoutUpdate } from '../models/ProjectLayoutUpdate';
import type { ProjectListResponse } from '../models/ProjectListResponse';
import type { ProjectRead } from '../models/ProjectRead';
import type { ProjectRoomsReplace } from '../models/ProjectRoomsReplace';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ProjectsService {
    /**
     * 列出客户项目
     * 按时间倒序返回客户项目列表(含房间清单)。
     * @param skip 分页起始位置
     * @param limit 每页最大条数
     * @returns ProjectListResponse Successful Response
     * @throws ApiError
     */
    public static listProjectsApiV1ProjectsGet(
        skip?: number,
        limit: number = 50,
    ): CancelablePromise<ProjectListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/projects',
            query: {
                'skip': skip,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 新建客户项目
     * 创建一个新项目。平面图文件本身通过 `/agents` 上传与解析。
     * @param requestBody
     * @returns ProjectRead Successful Response
     * @throws ApiError
     */
    public static createProjectApiV1ProjectsPost(
        requestBody: ProjectCreate,
    ): CancelablePromise<ProjectRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/projects',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 查单个项目
     * 按 id 查一个项目的所有房间清单、平面图元数据。
     * @param projectId
     * @returns ProjectRead Successful Response
     * @throws ApiError
     */
    public static getProjectApiV1ProjectsProjectIdGet(
        projectId: number,
    ): CancelablePromise<ProjectRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/projects/{project_id}',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 删除项目
     * 删除项目并级联删除其房间、设计方案、报价单。
     * @param projectId
     * @returns void
     * @throws ApiError
     */
    public static deleteProjectApiV1ProjectsProjectIdDelete(
        projectId: number,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/projects/{project_id}',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 整组替换房间清单
     * 接受平面图解析后给出的房间清单,或让用户批量修改后整组提交。会清空已有房间再插入新列表。
     * @param projectId
     * @param requestBody
     * @returns ProjectRead Successful Response
     * @throws ApiError
     */
    public static replaceRoomsApiV1ProjectsProjectIdRoomsPut(
        projectId: number,
        requestBody: ProjectRoomsReplace,
    ): CancelablePromise<ProjectRead> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/projects/{project_id}/rooms',
            path: {
                'project_id': projectId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 读取平面图布局
     * 返回 `Project.floor_plan_layout` 解析后的房间坐标 + 旋转角。
     * @param projectId
     * @returns ProjectLayoutResponse Successful Response
     * @throws ApiError
     */
    public static getLayoutApiV1ProjectsProjectIdLayoutGet(
        projectId: number,
    ): CancelablePromise<ProjectLayoutResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/projects/{project_id}/layout',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * 保存平面图布局
     * 把 FloorPlanCanvas 上房间的位置 + 旋转角持久化。 不在当前项目房间清单里的 `room_id` 会被静默丢弃。
     * @param projectId
     * @param requestBody
     * @returns ProjectLayoutResponse Successful Response
     * @throws ApiError
     */
    public static putLayoutApiV1ProjectsProjectIdLayoutPut(
        projectId: number,
        requestBody: ProjectLayoutUpdate,
    ): CancelablePromise<ProjectLayoutResponse> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/projects/{project_id}/layout',
            path: {
                'project_id': projectId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
