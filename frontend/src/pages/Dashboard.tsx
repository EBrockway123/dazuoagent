export function Dashboard() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">工作台</h1>
      <p className="text-slate-600 text-sm">从这里开始一个新项目,或者继续上次的方案。</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <a href="/projects" className="card p-5 hover:shadow-md transition">
          <div className="text-lg font-medium">客户项目</div>
          <div className="text-sm text-slate-500 mt-1">查看 / 创建项目</div>
        </a>
        <a href="/materials" className="card p-5 hover:shadow-md transition">
          <div className="text-lg font-medium">素材库</div>
          <div className="text-sm text-slate-500 mt-1">板材 / 贴皮 / 五金</div>
        </a>
        <a href="/quotations" className="card p-5 hover:shadow-md transition">
          <div className="text-lg font-medium">报价单</div>
          <div className="text-sm text-slate-500 mt-1">查看历史报价</div>
        </a>
      </div>
    </div>
  );
}