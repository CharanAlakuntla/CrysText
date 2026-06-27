import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import App from "./App";
import "./index.css";

// Apply dark mode class on initial load from persisted state
try {
  const stored = JSON.parse(localStorage.getItem("crystext-store") || "{}");
  const isDark = stored?.state?.darkMode ?? true;
  if (isDark) document.documentElement.classList.add("dark");
  else document.documentElement.classList.remove("dark");
} catch {
  document.documentElement.classList.add("dark");
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 1000 * 60 * 5, retry: 1 },
  },
});

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#1a2030",
            color: "#f3f4f6",
            border: "1px solid rgba(255,255,255,0.08)",
          },
        }}
      />
    </QueryClientProvider>
  </React.StrictMode>
);
