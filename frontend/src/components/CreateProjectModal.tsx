/**
 * CreateProjectModal — modal form for a new customer project.
 *
 * Fields:
 *   - name, customer_name, customer_phone (optional), address (optional)
 *   - rooms: dynamic list of (name, width_mm, length_mm). Always starts
 *     with one empty row so the user can either fill it or remove it.
 *
 * On submit → calls `projectsApi.create()` → on success navigates to
 * /projects/:id and onSaved callback fires (so parent can refresh).
 *
 * No external UI lib — plain Tailwind + a small backdrop/portal.
 */

import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { projectsApi, type CreateProjectPayload } from "@/lib/api";
import type { RoomCreatePayload } from "@/types";

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved?: () => void;
}

interface DraftRoom {
  name: string;
  width_mm: string;
  length_mm: string;
}

const EMPTY_ROOM = (): DraftRoom => ({ name: "", width_mm: "", length_mm: "" });

export function CreateProjectModal({ open, onClose, onSaved }: Props) {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [address, setAddress] = useState("");
  const [rooms, setRooms] = useState<DraftRoom[]>([EMPTY_ROOM()]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const nameInputRef = useRef<HTMLInputElement>(null);

  // Reset state when the modal opens; autofocus the first input.
  useEffect(() => {
    if (!open) return;
    setName("");
    setCustomerName("");
    setCustomerPhone("");
    setAddress("");
    setRooms([EMPTY_ROOM()]);
    setSubmitting(false);
    setError(null);
    // Defer focus until after the dialog paints.
    const id = setTimeout(() => nameInputRef.current?.focus(), 0);
    return () => clearTimeout(id);
  }, [open]);

  // ESC closes the modal (matching native dialog conventions).
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const canSubmit =
    name.trim().length > 0 &&
    customerName.trim().length > 0 &&
    !submitting;

  function updateRoom(idx: number, patch: Partial<DraftRoom>) {
    setRooms((prev) => prev.map((r, i) => (i === idx ? { ...r, ...patch } : r)));
  }

  function addRoom() {
    setRooms((prev) => [...prev, EMPTY_ROOM()]);
  }

  function removeRoom(idx: number) {
    setRooms((prev) => (prev.length === 1 ? prev : prev.filter((_, i) => i !== idx)));
  }

  async function submit() {
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);

    // Build payload, filtering out empty room rows.
    const cleanRooms: RoomCreatePayload[] = [];
    for (const r of rooms) {
      if (!r.name.trim()) continue;
      const w = Number(r.width_mm);
      const l = Number(r.length_mm);
      if (!Number.isFinite(w) || !Number.isFinite(l) || w < 0 || l < 0) {
        setError(`房间"${r.name}"的尺寸需要是有效数字`);
        setSubmitting(false);
        return;
      }
      cleanRooms.push({
        name: r.name.trim(),
        width_mm: w,
        length_mm: l,
        area_sqm: (w * l) / 1_000_000,
      });
    }

    const payload: CreateProjectPayload = {
      name: name.trim(),
      customer_name: customerName.trim(),
      customer_phone: customerPhone.trim() || null,
      address: address.trim() || null,
      rooms: cleanRooms,
    };

    try {
      const created = await projectsApi.create(payload);
      onSaved?.();
      onClose();
      // Navigate after the modal closes so the user lands on the
      // newly-created project's detail page.
      navigate(`/projects/${created.id}`);
    } catch (err) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail;
      setError(detail ?? (err instanceof Error ? err.message : "创建失败"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onMouseDown={(e) => {
        // Click on the backdrop closes; clicks inside the dialog don't
        // (stopPropagation handled by the inner element).
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="card w-full max-w-lg max-h-[90vh] overflow-auto"
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-project-title"
      >
        <div className="px-5 py-4 border-b flex items-center justify-between">
          <h2 id="create-project-title" className="font-medium">
            新建客户项目
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600"
            aria-label="关闭"
          >
            ✕
          </button>
        </div>

        <div className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <label className="block col-span-2">
              <span className="text-sm text-slate-600">项目名称 *</span>
              <input
                ref={nameInputRef}
                className="mt-1 w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="例如:星河湾 17-602"
                value={name}
                onChange={(e) => setName(e.target.value)}
                data-testid="create-project-name"
              />
            </label>
            <label className="block">
              <span className="text-sm text-slate-600">客户名 *</span>
              <input
                className="mt-1 w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="客户姓名"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                data-testid="create-project-customer"
              />
            </label>
            <label className="block">
              <span className="text-sm text-slate-600">联系电话</span>
              <input
                className="mt-1 w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="可选"
                value={customerPhone}
                onChange={(e) => setCustomerPhone(e.target.value)}
              />
            </label>
            <label className="block col-span-2">
              <span className="text-sm text-slate-600">项目地址</span>
              <input
                className="mt-1 w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="可选"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
              />
            </label>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-600">
                房间清单 <span className="text-slate-400">(可后补)</span>
              </span>
              <button
                type="button"
                onClick={addRoom}
                className="text-sm text-brand-600 hover:text-brand-700"
              >
                + 添加房间
              </button>
            </div>
            <div className="space-y-2">
              {rooms.map((room, idx) => (
                <div key={idx} className="flex gap-2 items-center">
                  <input
                    className="flex-1 border border-slate-300 rounded-md px-2 py-1.5 text-sm"
                    placeholder="房间名(如:主卧)"
                    value={room.name}
                    onChange={(e) => updateRoom(idx, { name: e.target.value })}
                  />
                  <input
                    type="number"
                    min={0}
                    className="w-24 border border-slate-300 rounded-md px-2 py-1.5 text-sm"
                    placeholder="宽 mm"
                    value={room.width_mm}
                    onChange={(e) =>
                      updateRoom(idx, { width_mm: e.target.value })
                    }
                  />
                  <input
                    type="number"
                    min={0}
                    className="w-24 border border-slate-300 rounded-md px-2 py-1.5 text-sm"
                    placeholder="长 mm"
                    value={room.length_mm}
                    onChange={(e) =>
                      updateRoom(idx, { length_mm: e.target.value })
                    }
                  />
                  {rooms.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeRoom(idx)}
                      className="text-slate-400 hover:text-red-500 px-1"
                      aria-label={`删除房间 ${idx + 1}`}
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-md px-3 py-2">
              {error}
            </div>
          )}
        </div>

        <div className="px-5 py-4 border-t flex items-center justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="px-4 py-2 text-sm text-slate-600 hover:text-slate-800"
          >
            取消
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={!canSubmit}
            className="btn-primary"
            data-testid="create-project-submit"
          >
            {submitting ? "创建中…" : "创建"}
          </button>
        </div>
      </div>
    </div>
  );
}