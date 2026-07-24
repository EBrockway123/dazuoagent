import { useState } from "react";
import { useParams } from "react-router-dom";
import { agentsApi } from "@/lib/api";
import type { ChatMessage } from "@/types";

// DesignStudio is the heart of the editor: 2D floor plan on the left, 3D
// preview on the right, and an Agent chat panel docked at the bottom.
// Today only the chat panel is wired — the 2D/3D surfaces are placeholders.

export function DesignStudio() {
  const { projectId } = useParams();
  const id = Number(projectId);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "你好!我是你的定制设计助理。告诉我你想要的风格、预算,我来帮你搭方案。" },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  const send = async () => {
    const text = input.trim();
    if (!text) return;
    const next = [...messages, { role: "user" as const, content: text }];
    setMessages(next);
    setInput("");
    setBusy(true);
    try {
      const res = await agentsApi.chat(id, next);
      setMessages((m) => [...m, { role: "assistant", content: res.reply }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid grid-cols-12 gap-4 h-[calc(100vh-7rem)]">
      {/* 2D plan placeholder */}
      <section className="card col-span-5 flex flex-col">
        <div className="px-4 py-3 border-b font-medium text-sm">2D 平面图</div>
        <div className="flex-1 grid place-items-center text-slate-400 text-sm">
          <span>上传平面图后在此显示房间与家具布局</span>
        </div>
      </section>

      {/* 3D preview placeholder */}
      <section className="card col-span-7 flex flex-col">
        <div className="px-4 py-3 border-b font-medium text-sm">3D 预览 (Three.js)</div>
        <div className="flex-1 grid place-items-center text-slate-400 text-sm">
          <span>react-three-fiber 场景占位 — 后续接入</span>
        </div>
      </section>

      {/* Chat panel */}
      <section className="card col-span-12 flex flex-col">
        <div className="px-4 py-3 border-b font-medium text-sm">设计助理</div>
        <div className="flex-1 overflow-auto p-4 space-y-3">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`max-w-2xl rounded-lg px-3 py-2 text-sm ${
                m.role === "user" ? "ml-auto bg-brand-500 text-white" : "bg-slate-100 text-slate-800"
              }`}
            >
              {m.content}
            </div>
          ))}
        </div>
        <div className="border-t p-3 flex gap-2">
          <input
            className="flex-1 border border-slate-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            placeholder="比如:主卧 18 ㎡,做一个到顶的大衣柜,白色哑光,预算 1.5 万"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
          />
          <button className="btn-primary" disabled={busy} onClick={send}>
            {busy ? "发送中…" : "发送"}
          </button>
        </div>
      </section>
    </div>
  );
}