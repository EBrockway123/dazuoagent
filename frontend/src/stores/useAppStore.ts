// Cross-cutting app state. Keep narrow — page-local state belongs to the page.

import { create } from "zustand";

interface AppState {
  currentProjectId: number | null;
  setCurrentProject: (id: number | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentProjectId: null,
  setCurrentProject: (id) => set({ currentProjectId: id }),
}));