import { useEffect, useState } from "react";
import { materialsApi } from "@/lib/api";
import type { Material } from "@/types";
import { formatCurrency } from "@/lib/utils";

export function MaterialLibrary() {
  const [items, setItems] = useState<Material[]>([]);
  const [keyword, setKeyword] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    materialsApi.list({ keyword: keyword || undefined }).then((res) => {
      setItems(res.items);
      setLoading(false);
    });
  }, [keyword]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">素材库</h1>
        <input
          type="search"
          placeholder="搜索 SKU / 名称…"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          className="border border-slate-300 rounded-md px-3 py-2 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
      </div>

      {loading ? (
        <div className="text-slate-500 text-sm">加载中…</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((m) => (
            <div key={m.id} className="card p-4">
              <div
                className="h-24 rounded-md mb-3 border"
                style={{ background: m.color_code ?? "#f1f5f9" }}
              />
              <div className="font-medium text-sm">{m.name}</div>
              <div className="text-xs text-slate-500 mt-0.5">
                {m.board_type ?? m.hardware_category ?? "—"}
                {m.thickness_mm ? ` · ${m.thickness_mm} mm` : ""}
                {m.veneer ? ` · ${m.veneer}` : ""}
              </div>
              <div className="flex items-center justify-between mt-3">
                <span className="text-xs text-slate-400">{m.sku}</span>
                <span className="font-semibold text-brand-700">
                  {formatCurrency(m.price)} / {m.unit === "sqm" ? "㎡" : m.unit}
                </span>
              </div>
            </div>
          ))}
          {items.length === 0 && (
            <div className="col-span-full text-center text-slate-500 text-sm py-10">
              暂无素材。先在 backend 跑{" "}
              <code className="bg-slate-100 px-1 rounded">python -m dazuoagent.db.seed</code> 写入示例。
            </div>
          )}
        </div>
      )}
    </div>
  );
}