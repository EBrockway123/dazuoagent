// Axios client with the base URL proxied by Vite (see vite.config.ts).

import axios from "axios";

export const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
});

// Domain endpoints. Each returns the typed payload — no `any` leaks past this layer.

import type {
  ChatMessage,
  ChatResponse,
  Design,
  Material,
  Project,
  Quotation,
} from "@/types";

export const materialsApi = {
  list: (params?: {
    board_type?: string;
    veneer?: string;
    keyword?: string;
  }) => api.get<{ items: Material[]; total: number }>("/materials", { params }).then((r) => r.data),
  get: (id: number) => api.get<Material>(`/materials/${id}`).then((r) => r.data),
};

export const projectsApi = {
  list: () => api.get<{ items: Project[]; total: number }>("/projects").then((r) => r.data),
  get: (id: number) => api.get<Project>(`/projects/${id}`).then((r) => r.data),
};

export const designsApi = {
  get: (id: number) => api.get<Design>(`/designs/${id}`).then((r) => r.data),
};

export const quotationsApi = {
  get: (id: number) => api.get<Quotation>(`/quotations/${id}`).then((r) => r.data),
};

export const agentsApi = {
  chat: (projectId: number | null, messages: ChatMessage[]) =>
    api
      .post<ChatResponse>("/agents/chat", { project_id: projectId, messages })
      .then((r) => r.data),

  parseFloorplan: (projectId: number, file: File, mode: "agent" | "ocr" = "agent") => {
    const form = new FormData();
    form.append("file", file);
    form.append("mode", mode);
    return api
      .post<{ status: string; rooms: Array<{ name: string; width_mm: number | null; length_mm: number | null; area_sqm: number | null }> }>(
        `/agents/projects/${projectId}/parse-floorplan`,
        form,
        { headers: { "Content-Type": "multipart/form-data" } },
      )
      .then((r) => r.data);
  },
};