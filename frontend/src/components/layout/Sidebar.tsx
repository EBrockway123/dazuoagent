import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";

const links = [
  { to: "/", label: "工作台", end: true },
  { to: "/projects", label: "客户项目" },
  { to: "/materials", label: "素材库" },
  { to: "/quotations", label: "报价单" },
];

export function Sidebar() {
  return (
    <aside className="w-56 shrink-0 border-r border-slate-200 bg-white">
      <div className="px-6 py-5">
        <div className="text-lg font-semibold text-brand-700">dazuoagent</div>
        <div className="text-xs text-slate-500">全屋定制设计平台</div>
      </div>
      <nav className="px-2 pb-4 space-y-1">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.end}
            className={({ isActive }) =>
              cn(
                "block rounded-md px-3 py-2 text-sm",
                isActive ? "bg-brand-50 text-brand-700 font-medium" : "text-slate-700 hover:bg-slate-100",
              )
            }
          >
            {l.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}