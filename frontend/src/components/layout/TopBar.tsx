export function TopBar() {
  return (
    <header className="h-14 border-b border-slate-200 bg-white px-6 flex items-center justify-between">
      <div className="text-sm text-slate-500">MVP 框架搭建中</div>
      <div className="flex items-center gap-2">
        <button className="btn-ghost text-sm">登录</button>
      </div>
    </header>
  );
}