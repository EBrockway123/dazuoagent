import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { agentsApi, projectsApi } from "@/lib/api";
import type { Project } from "@/types";
import { formatArea } from "@/lib/utils";

interface SuggestedRoom {
  name: string;
  width_mm: number | null;
  length_mm: number | null;
  area_sqm: number | null;
}

export function ProjectDetail() {
  const { projectId } = useParams();
  const id = Number(projectId);
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [suggested, setSuggested] = useState<SuggestedRoom[] | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    projectsApi
      .get(id)
      .then(setProject)
      .finally(() => setLoading(false));
  }, [id]);

  const onUpload = async (file: File) => {
    setUploading(true);
    try {
      const res = await agentsApi.parseFloorplan(id, file, "agent");
      setSuggested(res.rooms);
    } finally {
      setUploading(false);
    }
  };

  if (loading) return <div className="text-slate-500 text-sm">加载中…</div>;
  if (!project) return <div className="text-slate-500 text-sm">项目不存在。</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{project.name}</h1>
          <div className="text-sm text-slate-500">
            {project.customer_name} · {project.customer_phone ?? "未填电话"}
          </div>
        </div>
        <Link to={`/projects/${id}/design`} className="btn-primary">
          进入设计工作室 →
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="card p-5 lg:col-span-2">
          <h2 className="font-medium mb-3">房间清单</h2>
          {project.rooms.length === 0 ? (
            <div className="text-sm text-slate-500">
              还没有房间。上传平面图后,Agent 会帮你识别出来。
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="text-left text-slate-500 border-b">
                <tr>
                  <th className="py-2">名称</th>
                  <th>尺寸</th>
                  <th>面积</th>
                </tr>
              </thead>
              <tbody>
                {project.rooms.map((r) => (
                  <tr key={r.id} className="border-b last:border-0">
                    <td className="py-2">{r.name}</td>
                    <td>
                      {r.width_mm} × {r.length_mm} mm
                    </td>
                    <td>{formatArea(r.area_sqm)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="card p-5">
          <h2 className="font-medium mb-3">平面图</h2>
          <input
            ref={fileInput}
            type="file"
            accept="image/*,application/pdf"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) onUpload(f);
            }}
          />
          <button
            className="btn-primary w-full"
            disabled={uploading}
            onClick={() => fileInput.current?.click()}
          >
            {uploading ? "上传中…" : "上传平面图"}
          </button>
          {project.floor_plan_file && (
            <div className="text-xs text-slate-500 mt-2 truncate">{project.floor_plan_file}</div>
          )}

          {suggested && (
            <div className="mt-4">
              <div className="text-sm font-medium mb-2">识别出的房间(待确认)</div>
              <ul className="space-y-1 text-sm">
                {suggested.map((r, i) => (
                  <li key={i} className="flex justify-between border-b last:border-0 py-1">
                    <span>{r.name}</span>
                    <span className="text-slate-500">
                      {r.area_sqm ? formatArea(r.area_sqm) : "—"}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}