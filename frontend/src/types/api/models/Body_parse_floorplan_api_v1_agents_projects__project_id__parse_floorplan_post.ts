/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Body_parse_floorplan_api_v1_agents_projects__project_id__parse_floorplan_post = {
    /**
     * 平面图文件(JPG / PNG / PDF)。
     */
    file: string;
    /**
     * 解析模式:`agent` = LLM 视觉(默认),`ocr` = OCR 走通模式。
     */
    mode?: string;
};

