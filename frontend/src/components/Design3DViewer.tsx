/**
 * Design3DViewer — react-three-fiber 渲染项目房间 + 家具的 3D 场景。
 *
 * 复用 `FloorPlanCanvas` 已经写入的 `Project.floor_plan_layout`(房间空间位置)
 * —— 不需要再拉一遍后端。
 *
 * 坐标系换算:
 *   - 后端 2D 用 mm,X = 横, Y = 纵(房间内 depth 方向)
 *   - Three.js 用米,X = 横, Y = 上(高度), Z = 纵
 *   - 所以 2D (x, y) → 3D (x/1000, 0, y/1000);2D 旋转 → 绕 Y 轴顺时针
 *
 * 暂不做墙(只有地板平面 + 家具盒),让首版专注于"东西摆在哪"。
 */

import { Canvas } from "@react-three/fiber";
import { Grid, Html, OrbitControls } from "@react-three/drei";
import { useMemo } from "react";
import * as THREE from "three";

import type { Design, Furniture, Project, Room, RoomLayoutItem } from "@/types";

interface Props {
  project: Project;
}

interface SceneRoom {
  id: number;
  name: string;
  /** 居中点 X/Z (米)。 */
  center: [number, number];
  /** 长宽 (米)。 */
  size: [number, number];
  /** 顺时针绕 Y 轴旋转 (rad)。 */
  rotation: number;
}

interface SceneFurniture {
  id: number;
  label: string;
  type: string;
  /** 中心点 X/Z/Y (米);Y 为底面到地面的高度。 */
  center: [number, number, number];
  size: [number, number, number];
}

interface SceneData {
  rooms: SceneRoom[];
  furniture: SceneFurniture[];
  /** 镜头初始位置 —— 居中俯视场景外圈 +1m 高度。 */
  cameraStart: [number, number, number];
}

const MM_PER_M = 1000;
const FURNITURE_COLOR = "#c19a6b"; // 默认木色
const ROOM_COLORS = ["#fde2e2", "#dcfce7", "#dbeafe", "#fef3c7", "#e9d5ff", "#fbcfe8"];
const EMPTY_HEIGHT_M = 0.05;

export function Design3DViewer({ project }: Props) {
  const data = useMemo(() => buildSceneData(project), [project]);

  return (
    <div className="relative w-full h-full">
      <Canvas
        shadows
        camera={{ position: data.cameraStart, fov: 45 }}
        gl={{ preserveDrawingBuffer: true, antialias: true }}
      >
        <color attach="background" args={["#f1f5f9"]} />
        <ambientLight intensity={0.7} />
        <directionalLight
          position={[10, 15, 10]}
          intensity={0.8}
          castShadow
          shadow-mapSize={[1024, 1024]}
        />
        <directionalLight position={[-10, 8, -5]} intensity={0.2} />

        <Grid
          args={[40, 40]}
          cellSize={0.5}
          cellThickness={0.5}
          cellColor="#cbd5e1"
          sectionSize={2}
          sectionThickness={1}
          sectionColor="#94a3b8"
          fadeDistance={30}
          fadeStrength={1.5}
          position={[0, -0.001, 0]}
          infiniteGrid={false}
        />

        {data.rooms.map((room) => (
          <RoomFloor key={room.id} room={room} />
        ))}

        {data.furniture.map((item) => (
          <FurnitureBox key={item.id} item={item} />
        ))}

        <OrbitControls
          enableDamping
          dampingFactor={0.1}
          maxPolarAngle={Math.PI / 2 - 0.05}
          minDistance={2}
          maxDistance={40}
          target={[data.cameraStart[0], 0, data.cameraStart[2]]}
        />
      </Canvas>

      <SceneLegend data={data} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// 子组件
// ---------------------------------------------------------------------------

function RoomFloor({ room }: { room: SceneRoom }) {
  // 用一个非常薄的 Box(地板厚度)而不是 planeGeometry,这样从任何角度都可见
  return (
    <group
      position={[room.center[0], EMPTY_HEIGHT_M / 2, room.center[1]]}
      rotation={[0, room.rotation, 0]}
    >
      <mesh receiveShadow>
        <boxGeometry args={[room.size[0], EMPTY_HEIGHT_M, room.size[1]]} />
        <meshStandardMaterial color={pickRoomColor(room.id)} transparent opacity={0.85} />
      </mesh>
      {/* 房间边框线 */}
      <lineSegments>
        <edgesGeometry args={[new THREE.BoxGeometry(room.size[0], EMPTY_HEIGHT_M, room.size[1])]} />
        <lineBasicMaterial color="#475569" />
      </lineSegments>
      {/* 房名标注 */}
      <Html
        position={[0, 0.6, 0]}
        center
        style={{
          pointerEvents: "none",
          userSelect: "none",
          background: "rgba(15,23,42,0.85)",
          color: "white",
          padding: "2px 8px",
          borderRadius: 4,
          fontSize: 12,
          whiteSpace: "nowrap",
        }}
      >
        {room.name}
      </Html>
    </group>
  );
}

function FurnitureBox({ item }: { item: SceneFurniture }) {
  return (
    <group position={item.center}>
      <mesh castShadow receiveShadow>
        <boxGeometry args={item.size} />
        <meshStandardMaterial color={FURNITURE_COLOR} roughness={0.7} metalness={0.05} />
      </mesh>
      <Html
        position={[0, item.size[1] / 2 + 0.15, 0]}
        center
        style={{
          pointerEvents: "none",
          userSelect: "none",
          background: "rgba(255,255,255,0.9)",
          color: "#0f172a",
          padding: "1px 6px",
          borderRadius: 3,
          fontSize: 10,
          whiteSpace: "nowrap",
          border: "1px solid #cbd5e1",
        }}
      >
        {item.label}
      </Html>
    </group>
  );
}

function SceneLegend({ data }: { data: SceneData }) {
  return (
    <div className="absolute top-2 left-2 card p-3 text-xs space-y-1">
      <div className="font-medium text-slate-700">场景信息</div>
      <div className="text-slate-500">房间: {data.rooms.length}</div>
      <div className="text-slate-500">家具: {data.furniture.length}</div>
      <div className="text-slate-400 mt-1">左键拖动 / 滚轮缩放 / 右键平移</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 数据准备:Project → SceneData
// ---------------------------------------------------------------------------

function buildSceneData(project: Project): SceneData {
  const layoutItems = parseLayoutItems(project.floor_plan_layout);
  const rooms: SceneRoom[] = project.rooms.map((room, idx) => {
    const item = layoutItems.get(room.id);
    const fallbackX = sumWidthsBefore(project.rooms, idx);
    const cxMm = item?.x_mm ?? fallbackX;
    const cyMm = item?.y_mm ?? 0;
    return {
      id: room.id,
      name: room.name,
      center: [cxMm / MM_PER_M, cyMm / MM_PER_M],
      size: [room.width_mm / MM_PER_M, room.length_mm / MM_PER_M],
      rotation: degreesToRadians(item?.rotation_deg ?? 0),
    };
  });

  // 家具:优先按 room_id 锚定到房间中心,否则放原点
  const roomCenterById = new Map<number, [number, number]>(
    rooms.map((r) => [r.id, r.center]),
  );
  const furniture: SceneFurniture[] = project.designs.flatMap((design) =>
    design.furniture.map((piece) => buildSceneFurniture(piece, design, roomCenterById)),
  );

  return {
    rooms,
    furniture,
    cameraStart: computeCameraStart(rooms, furniture),
  };
}

function buildSceneFurniture(
  piece: Furniture,
  design: Design,
  roomCenterById: Map<number, [number, number]>,
): SceneFurniture {
  const w = piece.width_mm / MM_PER_M;
  const h = piece.height_mm / MM_PER_M;
  const d = piece.depth_mm / MM_PER_M;
  const center = roomCenterById.get(piece.room_id ?? -1);
  return {
    id: piece.id,
    label: `${piece.label}${design.is_final ? " (final)" : ""}`,
    type: piece.type,
    center: [center?.[0] ?? 0, h / 2, center?.[1] ?? 0],
    size: [w, h, d],
  };
}

function parseLayoutItems(json: string | null): Map<number, RoomLayoutItem> {
  const out = new Map<number, RoomLayoutItem>();
  if (!json) return out;
  try {
    const data = JSON.parse(json);
    if (data && Array.isArray(data.rooms)) {
      for (const item of data.rooms) {
        if (typeof item.room_id === "number") {
          out.set(item.room_id, item as RoomLayoutItem);
        }
      }
    }
  } catch {
    /* ignore malformed layout */
  }
  return out;
}

function sumWidthsBefore(rooms: Room[], idx: number): number {
  let sum = 0;
  for (let i = 0; i < idx; i++) sum += rooms[i].width_mm;
  return sum;
}

function degreesToRadians(deg: number): number {
  return (deg * Math.PI) / 180;
}

function pickRoomColor(id: number): string {
  return ROOM_COLORS[id % ROOM_COLORS.length];
}

function computeCameraStart(
  rooms: SceneRoom[],
  furniture: SceneFurniture[],
): [number, number, number] {
  // 取所有房间 + 家具的 X/Z 包络,从中点后退 12m、高 12m
  const all: Array<[number, number]> = [];
  rooms.forEach((r) => all.push(r.center));
  furniture.forEach((f) => all.push([f.center[0], f.center[2]]));
  if (all.length === 0) return [8, 8, 8];

  let minX = Infinity, maxX = -Infinity, minZ = Infinity, maxZ = -Infinity;
  for (const [x, z] of all) {
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    if (z < minZ) minZ = z;
    if (z > maxZ) maxZ = z;
  }
  const cx = (minX + maxX) / 2;
  const cz = (minZ + maxZ) / 2;
  const span = Math.max(maxX - minX, maxZ - minZ, 4);
  return [cx + span * 0.9, span * 0.85, cz + span * 0.9];
}