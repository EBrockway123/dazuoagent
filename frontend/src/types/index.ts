// Shared API types. Keep in sync with backend/src/dazuoagent/schemas/*.py.

export type BoardType = "particleboard" | "multilayer" | "mdf" | "solid_wood";
export type Veneer = "melamine" | "paint" | "pvc" | "wood_veneer" | "wrap";
export type HardwareCategory = "hinge" | "slide" | "handle" | "lift";
export type FurnitureType =
  | "wardrobe"
  | "kitchen_cabinet"
  | "tv_stand"
  | "bookcase"
  | "shoe_cabinet"
  | "wardrobe_open"
  | "other";

export interface Material {
  id: number;
  sku: string;
  name: string;
  board_type: BoardType | null;
  thickness_mm: number | null;
  veneer: Veneer | null;
  hardware_category: HardwareCategory | null;
  color_code: string | null;
  image_url: string | null;
  supplier: string | null;
  price: number;
  unit: string;
}

export interface Room {
  id: number;
  project_id: number;
  name: string;
  width_mm: number;
  length_mm: number;
  area_sqm: number;
  openings: string | null;
}

export interface Project {
  id: number;
  name: string;
  customer_name: string;
  customer_phone: string | null;
  address: string | null;
  floor_plan_file: string | null;
  floor_plan_layout: string | null;
  rooms: Room[];
  created_at: string;
  updated_at: string;
}

export interface Furniture {
  id: number;
  design_id: number;
  type: FurnitureType;
  label: string;
  width_mm: number;
  height_mm: number;
  depth_mm: number;
  material_id: number | null;
  room_id: number | null;
}

export interface Design {
  id: number;
  project_id: number;
  name: string;
  summary: string | null;
  is_final: boolean;
  furniture: Furniture[];
}

export interface QuotationLineItem {
  id: number;
  description: string;
  quantity: number;
  unit: string;
  unit_price: number;
  amount: number;
}

export interface Quotation {
  id: number;
  project_id: number;
  design_id: number | null;
  status: "draft" | "issued" | "accepted" | "rejected";
  subtotal: number;
  labor_cost: number;
  tax: number;
  total: number;
  notes: string | null;
  line_items: QuotationLineItem[];
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatResponse {
  reply: string;
  tool_calls: unknown[];
  suggested_actions: string[];
}