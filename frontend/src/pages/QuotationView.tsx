import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { quotationsApi } from "@/lib/api";
import type { Quotation } from "@/types";
import { formatCurrency } from "@/lib/utils";

export function QuotationView() {
  const { quotationId } = useParams();
  const id = Number(quotationId);
  const [quotation, setQuotation] = useState<Quotation | null>(null);
  const [loading, setLoading] = useState(!!id);

  useEffect(() => {
    if (!id) return;
    quotationsApi.get(id).then(setQuotation).finally(() => setLoading(false));
  }, [id]);

  if (!id) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">报价单</h1>
        <div className="card p-8 text-center text-slate-500 text-sm">
          报价单列表占位 —— 后续从项目详情跳转过来。
        </div>
      </div>
    );
  }

  if (loading) return <div className="text-slate-500 text-sm">加载中…</div>;
  if (!quotation) return <div className="text-slate-500 text-sm">报价单不存在。</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">报价单 #{quotation.id}</h1>
        <span className="text-xs px-2 py-1 rounded bg-slate-100 text-slate-600">{quotation.status}</span>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="px-4 py-2">项目</th>
              <th>数量</th>
              <th>单价</th>
              <th>金额</th>
            </tr>
          </thead>
          <tbody>
            {quotation.line_items.map((li) => (
              <tr key={li.id} className="border-t">
                <td className="px-4 py-2">{li.description}</td>
                <td>
                  {li.quantity} {li.unit}
                </td>
                <td>{formatCurrency(li.unit_price)}</td>
                <td>{formatCurrency(li.amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card p-4 ml-auto max-w-sm space-y-1 text-sm">
        <div className="flex justify-between">
          <span>小计</span>
          <span>{formatCurrency(quotation.subtotal)}</span>
        </div>
        <div className="flex justify-between">
          <span>人工 / 安装</span>
          <span>{formatCurrency(quotation.labor_cost)}</span>
        </div>
        <div className="flex justify-between">
          <span>税费</span>
          <span>{formatCurrency(quotation.tax)}</span>
        </div>
        <div className="flex justify-between font-semibold pt-2 border-t">
          <span>合计</span>
          <span className="text-brand-700">{formatCurrency(quotation.total)}</span>
        </div>
      </div>
    </div>
  );
}