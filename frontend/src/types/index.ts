// Type re-exports. Source of truth lives in the backend's Pydantic
// schemas; this file bridges the OpenAPI-generated `types/api/` tree to
// the shorter names the rest of the codebase uses.
//
// To regenerate the source tree, run:
//   npm run gen:types
// (requires the backend running on :8000; see package.json).

export type {
  MaterialRead as Material,
  MaterialListResponse as MaterialList,
  ProjectRead as Project,
  RoomRead as Room,
  DesignRead as Design,
  FurnitureRead as Furniture,
  QuotationRead as Quotation,
  QuotationLineItemRead as QuotationLineItem,
  RoomLayoutItem,
  RoomCreate as RoomCreatePayload,
  ProjectLayoutUpdate,
  ProjectRoomsReplace,
} from "./api";

// ChatMessage carries a discriminated `role` field — generated as a
// bare `string` (OpenAPI doesn't model union narrowing), so we restore
// the literal union here to keep the frontend's `switch (role)` checks
// type-safe.
export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

// Generated `ChatResponse.tool_calls` lands as `unknown[]`. We know it's
// `Array<{name, args}>` from the LangChain tool flow, so re-type it.
export interface ChatResponse {
  reply: string;
  tool_calls: Array<{ name?: string; args?: Record<string, unknown> }>;
  suggested_actions: string[];
}

// The OpenAPI generator emits the enums as plain string unions rather
// than the typed string-literal unions our components expect. Re-export
// them as literal unions so call sites stay exhaustive.
export type BoardType =
  | "particleboard"
  | "multilayer"
  | "mdf"
  | "solid_wood";
export type Veneer =
  | "melamine"
  | "paint"
  | "pvc"
  | "wood_veneer"
  | "wrap";
export type HardwareCategory =
  | "hinge"
  | "slide"
  | "handle"
  | "lift"
  | "rod";
export type FurnitureType =
  | "wardrobe"
  | "kitchen_cabinet"
  | "tv_stand"
  | "bookcase"
  | "shoe_cabinet"
  | "wardrobe_open"
  | "other";