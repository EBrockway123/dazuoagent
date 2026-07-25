import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { CreateProjectModal } from "@/components/CreateProjectModal";
import { projectsApi } from "@/lib/api";
import type { Project } from "@/types";

export function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);

  function refresh() {
    projectsApi.list().then((res) => {
      setProjects(res.items);
      setLoading(false);
    });
  }

  useEffect(refresh, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">客户项目</h1>
        <button
          className="btn-primary"
          onClick={() => setShowCreate(true)}
          data-testid="open-create-project"
        >
          + 新建项目
        </button>
      </div>

      {loading ? (
        <div className="text-slate-500 text-sm">加载中…</div>
      ) : projects.length === 0 ? (
        <div className="card p-8 text-center text-slate-500">
          还没有项目。先到{" "}
          <button
            className="text-brand-600 underline"
            onClick={() => setShowCreate(true)}
          >
            新建项目
          </button>{" "}
          试试。
        </div>
      ) : (
        <div className="card divide-y">
          {projects.map((p) => (
            <Link
              key={p.id}
              to={`/projects/${p.id}`}
              className="flex items-center justify-between p-4 hover:bg-slate-50"
            >
              <div>
                <div className="font-medium">{p.name}</div>
                <div className="text-xs text-slate-500">{p.customer_name} · {(p.rooms ?? []).length} 个房间</div>
              </div>
              <div className="text-xs text-slate-400">→</div>
            </Link>
          ))}
        </div>
      )}

      <CreateProjectModal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onSaved={refresh}
      />
    </div>
  );
}