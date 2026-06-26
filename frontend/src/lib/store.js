import { create } from "zustand";
import { persist } from "zustand/middleware";

export const useAppStore = create(
  persist(
    (set, get) => ({
      // Recent searches
      recentSearches: [],
      addRecentSearch: (q) => {
        const current = get().recentSearches.filter((s) => s !== q);
        set({ recentSearches: [q, ...current].slice(0, 8) });
      },
      clearRecentSearches: () => set({ recentSearches: [] }),

      // Compare list
      compareList: [],
      toggleCompare: (formula) => {
        const list = get().compareList;
        if (list.includes(formula)) {
          set({ compareList: list.filter((f) => f !== formula) });
        } else if (list.length < 4) {
          set({ compareList: [...list, formula] });
        }
      },
      clearCompare: () => set({ compareList: [] }),

      // Dark mode
      darkMode: true,
      toggleDarkMode: () => set((s) => ({ darkMode: !s.darkMode })),
    }),
    { name: "crystext-store" }
  )
);
