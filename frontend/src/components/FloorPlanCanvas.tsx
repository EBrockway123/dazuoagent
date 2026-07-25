/**
 * FloorPlanCanvas — 2D 平面图编辑器。
 *
 * 渲染项目房间清单,让用户:
 *   1. 拖拽房间在画布上摆位置
 *   2. 编辑房间名称 / 尺寸 / 删除
 *   3. 增删房间
 *   4. 一次性保存"房间清单" + "布局位置"两个变更
 *
 * 设计要点:
 *   - 坐标单位用 mm,viewBox 也是 mm,与数据库一致,避免来回转换
 *   - 房间没有 layout 时,自动横向排列一行作为兜底
 *   - 画布尺寸按最大房间边界 + 1m 边距自动撑开
 *   - 拖拽是 mouse 事件直接处理,不上第三方库
 */

import { useEffect, useMemo, useRef, useState } from "react";

import { projectsApi } from "@/lib/api";
import type { Project, Room, RoomLayoutItem } from "@/types";

interface Props {
  project: Project;
  /** 当成功保存后通知父组件刷新,通常用最新的 Project 替换掉。 */
  onSaved?: (project: Project) => void;
}

interface DraftRoom extends Room {
  /** 草稿模式下,未保存的新房间没有 id;用负数临时占位。 */
  isDraft?: boolean;
}

interface PositionState {
  x_mm: number;
  y_mm: number;
  rotation_deg: number;
}

const GRID_MM = 500; // 网格步长
const PADDING_MM = 1000; // 画布四边留白
const MIN_CANVAS_W = 8000;
const MIN_CANVAS_H = 6000;
const MAX_CANVAS_W = 40000;
const MAX_CANVAS_H = 30000;

export function FloorPlanCanvas({ project, onSaved }: Props) {
  // ---- 状态 --------------------------------------------------------------

  const [rooms, setRooms] = useState<DraftRoom[]>(project.rooms);
  const [positions, setPositions] = useState<Map<number, PositionState>>(() =>
    loadInitialPositions(project),
  );
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 项目切换时同步初始状态(避免深拷贝引用变化引起的奇怪重渲染)
  const projectId = project.id;
  useEffect(() => {
    setRooms(project.rooms);
    setPositions(loadInitialPositions(project));
    setSelectedId(null);
    setDirty(false);
    setError(null);
  }, [projectId]); // eslint-disable-line react-hooks/exhaustive-deps

  // ---- 派生 --------------------------------------------------------------

  const canvasSize = useMemo(() => {
    let maxX = 0;
    let maxY = 0;
    rooms.forEach((room, idx) => {
      const pos = positions.get(room.id) ?? defaultPositionFor(idx, rooms);
      maxX = Math.max(maxX, pos.x_mm + room.width_mm);
      maxY = Math.max(maxY, pos.y_mm + room.length_mm);
    });
    return {
      w: Math.min(MAX_CANVAS_W, Math.max(MIN_CANVAS_W, maxX + PADDING_MM)),
      h: Math.min(MAX_CANVAS_H, Math.max(MIN_CANVAS_H, maxY + PADDING_MM)),
    };
  }, [rooms, positions]);

  // ---- 拖拽 --------------------------------------------------------------

  const dragRef = useRef<{
    roomId: number;
    startX: number;
    startY: number;
    orig: PositionState;
  } | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  function onRoomMouseDown(roomId: number, e: React.MouseEvent) {
    e.stopPropagation();
    setSelectedId(roomId);
    const pos = positions.get(roomId);
    if (!pos) return;
    dragRef.current = {
      roomId,
      startX: e.clientX,
      startY: e.clientY,
      orig: { ...pos },
    };
  }

  function onMouseMove(e: React.MouseEvent) {
    const drag = dragRef.current;
    if (!drag) return;
    const svg = svgRef.current;
    if (!svg) return;
    // 屏幕 px → mm:用 viewBox 与 SVG bounding rect 比例换算
    const rect = svg.getBoundingClientRect();
    const pxPerMm = rect.width / canvasSize.w;
    const dxPx = e.clientX - drag.startX;
    const dyPx = e.clientY - drag.startY;
    const dxMm = dxPx / pxPerMm;
    const dyMm = dyPx / pxPerMm;
    // 吸附到 100mm 网格(更精细的吸附留给后续迭代)
    const snap = (v: number) => Math.round(v / 100) * 100;
    setPositions((prev) => {
      const next = new Map(prev);
      next.set(drag.roomId, {
        x_mm: Math.max(0, snap(drag.orig.x_mm + dxMm)),
        y_mm: Math.max(0, snap(drag.orig.y_mm + dyMm)),
        rotation_deg: drag.orig.rotation_deg,
      });
      return next;
    });
    setDirty(true);
  }

  function endDrag() {
    dragRef.current = null;
  }

  // ---- 房间编辑 ---------------------------------------------------------

  function patchSelectedRoom(patch: Partial<DraftRoom>) {
    if (selectedId == null) return;
    setRooms((prev) =>
      prev.map((r) => {
        if (r.id !== selectedId) return r;
        const next = { ...r, ...patch };
        // 改尺寸时同步更新面积
        if (patch.width_mm !== undefined || patch.length_mm !== undefined) {
          next.area_sqm = (next.width_mm * next.length_mm) / 1_000_000;
        }
        return next;
      }),
    );
    setDirty(true);
  }

  function addRoom() {
    const nextId = -1 * (rooms.length + 1); // 草稿 id 负数
    setRooms((prev) => [
      ...prev,
      {
        id: nextId,
        project_id: project.id,
        name: nextRoomName(prev),
        width_mm: 3000,
        length_mm: 3000,
        area_sqm: 9.0,
        openings: null,
        isDraft: true,
      },
    ]);
    setPositions((prev) => {
      const next = new Map(prev);
      const idx = rooms.length; // 即将成为的位置
      next.set(nextId, defaultPositionFor(idx, [...rooms, { id: nextId } as Room]));
      return next;
    });
    setSelectedId(nextId);
    setDirty(true);
  }

  function deleteSelected() {
    if (selectedId == null) return;
    setRooms((prev) => prev.filter((r) => r.id !== selectedId));
    setPositions((prev) => {
      const next = new Map(prev);
      next.delete(selectedId);
      return next;
    });
    setSelectedId(null);
    setDirty(true);
  }

  // ---- 保存 --------------------------------------------------------------

  async function save() {
    setSaving(true);
    setError(null);
    try {
      // 整体替换接口已经把"删旧建新"搞定 —— 直接整组提交即可
      const persistable = rooms.map((r) => ({
        name: r.name,
        width_mm: r.width_mm,
        length_mm: r.length_mm,
        area_sqm: r.area_sqm,
        openings: r.openings ?? null,
      }));
      const updated = await projectsApi.replaceRooms(project.id, persistable);

      // 2. 上传布局(只对已存在 id 写位置)
      const persistedIds = new Set(updated.rooms.map((r) => r.id));
      const layoutItems: RoomLayoutItem[] = [];
      rooms.forEach((room, idx) => {
        const pos = positions.get(room.id) ?? defaultPositionFor(idx, rooms);
        // 草稿 id → 映射回服务端给的真实 id(按顺序一一对应)
        const realId = updated.rooms[idx]?.id ?? room.id;
        if (!persistedIds.has(realId)) return;
        layoutItems.push({
          room_id: realId,
          x_mm: pos.x_mm,
          y_mm: pos.y_mm,
          rotation_deg: pos.rotation_deg,
        });
      });
      await projectsApi.updateLayout(project.id, layoutItems);

      // 3. 把"草稿"标记去掉,避免下次 dirty 计算错
      setRooms(updated.rooms.map((r) => ({ ...r, isDraft: false })));
      // 重建 positions:用真实 id
      const nextPositions = new Map<number, PositionState>();
      layoutItems.forEach((item) =>
        nextPositions.set(item.room_id, {
          x_mm: item.x_mm,
          y_mm: item.y_mm,
          rotation_deg: item.rotation_deg,
        }),
      );
      setPositions(nextPositions);
      setDirty(false);
      setSelectedId(null);
      onSaved?.(updated);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "保存失败";
      setError(msg);
    } finally {
      setSaving(false);
    }
  }

  // ---- 渲染 --------------------------------------------------------------

  const selectedRoom = rooms.find((r) => r.id === selectedId) ?? null;

  return (
    <div className="flex flex-col h-full gap-3">
      {/* 工具栏 */}
      <div className="flex items-center justify-between gap-2 text-sm">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={addRoom}
            className="btn-secondary"
            data-testid="floorplan-add-room"
          >
            + 添加房间
          </button>
          <span className="text-slate-400">
            {rooms.length} 个房间 · {Math.round(rooms.reduce((s, r) => s + r.area_sqm, 0) * 10) / 10} ㎡
          </span>
        </div>
        <div className="flex items-center gap-2">
          {dirty && <span className="text-amber-600 text-xs">有未保存的修改</span>}
          {error && <span className="text-red-600 text-xs">{error}</span>}
          <button
            type="button"
            onClick={save}
            disabled={!dirty || saving || rooms.length === 0}
            className="btn-primary"
          >
            {saving ? "保存中…" : "保存布局"}
          </button>
        </div>
      </div>

      {/* 画布 + 编辑面板 */}
      <div className="flex-1 grid grid-cols-12 gap-3 min-h-0">
        <div className="col-span-8 card overflow-auto p-2">
          <svg
            ref={svgRef}
            viewBox={`0 0 ${canvasSize.w} ${canvasSize.h}`}
            className="w-full h-full select-none"
            style={{ background: "#f8fafc" }}
            onMouseMove={onMouseMove}
            onMouseUp={endDrag}
            onMouseLeave={endDrag}
            onClick={() => setSelectedId(null)}
            data-testid="floorplan-svg"
          >
            {/* 网格 */}
            <GridLayer w={canvasSize.w} h={canvasSize.h} />
            {/* 房间 */}
            {rooms.map((room, idx) => {
              const pos = positions.get(room.id) ?? defaultPositionFor(idx, rooms);
              const isSelected = room.id === selectedId;
              return (
                <g
                  key={room.id}
                  transform={`translate(${pos.x_mm} ${pos.y_mm}) rotate(${pos.rotation_deg} ${room.width_mm / 2} ${room.length_mm / 2})`}
                  onMouseDown={(e) => onRoomMouseDown(room.id, e)}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedId(room.id);
                  }}
                  style={{ cursor: "grab" }}
                  data-testid={`floorplan-room-${room.id}`}
                >
                  <rect
                    width={room.width_mm}
                    height={room.length_mm}
                    fill={isSelected ? "#dbeafe" : "#ffffff"}
                    stroke={isSelected ? "#2563eb" : "#64748b"}
                    strokeWidth={isSelected ? 30 : 15}
                  />
                  <text
                    x={room.width_mm / 2}
                    y={room.length_mm / 2 - 100}
                    textAnchor="middle"
                    fontSize={Math.max(180, Math.min(room.width_mm, room.length_mm) / 8)}
                    fill="#1e293b"
                    style={{ pointerEvents: "none", userSelect: "none" }}
                  >
                    {room.name}
                  </text>
                  <text
                    x={room.width_mm / 2}
                    y={room.length_mm / 2 + 200}
                    textAnchor="middle"
                    fontSize={Math.max(140, Math.min(room.width_mm, room.length_mm) / 12)}
                    fill="#64748b"
                    style={{ pointerEvents: "none", userSelect: "none" }}
                  >
                    {room.width_mm} × {room.length_mm} mm · {room.area_sqm.toFixed(1)} ㎡
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* 编辑面板 */}
        <div className="col-span-4 card p-4 space-y-3">
          {selectedRoom ? (
            <RoomEditor
              room={selectedRoom}
              onPatch={patchSelectedRoom}
              onDelete={deleteSelected}
            />
          ) : (
            <div className="text-slate-500 text-sm">
              点击房间选中后,在右侧编辑名称 / 尺寸 / 删除。
              <br />
              拖动房间即可改变位置。
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 子组件
// ---------------------------------------------------------------------------

function RoomEditor({
  room,
  onPatch,
  onDelete,
}: {
  room: DraftRoom;
  onPatch: (patch: Partial<DraftRoom>) => void;
  onDelete: () => void;
}) {
  return (
    <div className="space-y-3 text-sm">
      <div className="font-medium text-slate-800">编辑房间</div>
      {room.isDraft && (
        <div className="text-xs text-amber-600">新房间,保存后才会入库。</div>
      )}
      <label className="block">
        <span className="text-slate-600">名称</span>
        <input
          className="mt-1 w-full border border-slate-300 rounded px-2 py-1"
          value={room.name}
          maxLength={64}
          onChange={(e) => onPatch({ name: e.target.value })}
          data-testid="floorplan-room-name"
        />
      </label>
      <div className="grid grid-cols-2 gap-2">
        <label className="block">
          <span className="text-slate-600">宽 (mm)</span>
          <input
            type="number"
            min={0}
            step={100}
            className="mt-1 w-full border border-slate-300 rounded px-2 py-1"
            value={room.width_mm}
            onChange={(e) => onPatch({ width_mm: Number(e.target.value) || 0 })}
          />
        </label>
        <label className="block">
          <span className="text-slate-600">长 (mm)</span>
          <input
            type="number"
            min={0}
            step={100}
            className="mt-1 w-full border border-slate-300 rounded px-2 py-1"
            value={room.length_mm}
            onChange={(e) => onPatch({ length_mm: Number(e.target.value) || 0 })}
          />
        </label>
      </div>
      <div className="text-slate-500 text-xs">面积: {room.area_sqm.toFixed(2)} ㎡</div>
      <button
        type="button"
        onClick={onDelete}
        className="w-full text-red-600 border border-red-200 rounded py-1 hover:bg-red-50"
      >
        删除该房间
      </button>
    </div>
  );
}

function GridLayer({ w, h }: { w: number; h: number }) {
  const lines: React.ReactElement[] = [];
  for (let x = 0; x <= w; x += GRID_MM) {
    lines.push(
      <line key={`v-${x}`} x1={x} y1={0} x2={x} y2={h} stroke="#e2e8f0" strokeWidth={10} />,
    );
  }
  for (let y = 0; y <= h; y += GRID_MM) {
    lines.push(
      <line key={`h-${y}`} x1={0} y1={y} x2={w} y2={y} stroke="#e2e8f0" strokeWidth={10} />,
    );
  }
  return <g>{lines}</g>;
}

// ---------------------------------------------------------------------------
// 工具函数
// ---------------------------------------------------------------------------

function loadInitialPositions(project: Project): Map<number, PositionState> {
  const map = new Map<number, PositionState>();
  let cursorX = PADDING_MM;
  const baseY = PADDING_MM;

  project.rooms.forEach((room) => {
    const saved = parseSavedLayout(project.floor_plan_layout).get(room.id);
    if (saved) {
      map.set(room.id, saved);
    } else {
      map.set(room.id, { x_mm: cursorX, y_mm: baseY, rotation_deg: 0 });
      cursorX += room.width_mm + GRID_MM;
    }
  });
  return map;
}

function parseSavedLayout(json: string | null): Map<number, PositionState> {
  const out = new Map<number, PositionState>();
  if (!json) return out;
  try {
    const data = JSON.parse(json);
    if (data && Array.isArray(data.rooms)) {
      for (const item of data.rooms) {
        if (typeof item.room_id === "number") {
          out.set(item.room_id, {
            x_mm: Number(item.x_mm) || 0,
            y_mm: Number(item.y_mm) || 0,
            rotation_deg: Number(item.rotation_deg) || 0,
          });
        }
      }
    }
  } catch {
    // 损坏的 JSON 当空处理
  }
  return out;
}

function defaultPositionFor(idx: number, rooms: Room[]): PositionState {
  let cursorX = PADDING_MM;
  for (let i = 0; i < idx; i++) {
    cursorX += (rooms[i]?.width_mm ?? 0) + GRID_MM;
  }
  return { x_mm: cursorX, y_mm: PADDING_MM, rotation_deg: 0 };
}

function nextRoomName(rooms: Room[]): string {
  const used = new Set(rooms.map((r) => r.name));
  const candidates = ["客厅", "主卧", "次卧", "厨房", "卫生间", "书房", "餐厅", "衣帽间"];
  for (const name of candidates) {
    if (!used.has(name)) return name;
  }
  return `房间 ${rooms.length + 1}`;
}