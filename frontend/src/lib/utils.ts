// Small UI helpers.

import clsx, { type ClassValue } from "clsx";

export const cn = (...inputs: ClassValue[]) => clsx(inputs);

export const formatCurrency = (value: number) =>
  new Intl.NumberFormat("zh-CN", { style: "currency", currency: "CNY", maximumFractionDigits: 0 }).format(value);

export const formatArea = (sqm: number) => `${sqm.toFixed(2)} ㎡`;