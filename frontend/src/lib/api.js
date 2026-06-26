import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  withCredentials: true,
  timeout: 30000,
});

// Attach JWT token to every request if present
api.interceptors.request.use((config) => {
  try {
    const stored = JSON.parse(localStorage.getItem("crystext-auth") || "{}");
    const token = stored?.state?.token;
    if (token) config.headers.Authorization = `Bearer ${token}`;
  } catch {}
  return config;
});

export const getMaterials = (params) => api.get("/materials", { params }).then((r) => r.data);
export const getMaterial = (formula) => api.get(`/material/${formula}`).then((r) => r.data);
export const searchMaterials = (body) => api.post("/search", body).then((r) => r.data);
export const getSuggestions = (q) => api.get("/suggestions", { params: { q } }).then((r) => r.data);
export const getSimilar = (formula) => api.get(`/similar/${formula}`).then((r) => r.data);
export const compareMaterials = (formulas) => api.post("/compare", { formulas }).then((r) => r.data);
export const getStats = () => api.get("/stats").then((r) => r.data);
export const getElements = () => api.get("/elements").then((r) => r.data);
export const getFavorites = () => api.get("/favorites").then((r) => r.data);
export const addFavorite = (formula) => api.post("/favorites", { formula }).then((r) => r.data);
export const removeFavorite = (formula) => api.delete(`/favorites/${formula}`).then((r) => r.data);

// Auth
export const registerUser = (data) => api.post("/auth/register", data).then((r) => r.data);
export const loginUser = (data) => api.post("/auth/login", data).then((r) => r.data);
export const getMe = () => api.get("/auth/me").then((r) => r.data);

export const getCifDownloadUrl = (formula) => `/api/download/cif/${formula}`;
export const getPdfDownloadUrl = (formula) => `/api/export/pdf/${formula}`;

export default api;
