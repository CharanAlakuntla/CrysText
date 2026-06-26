import { useState, useRef, useEffect, useCallback } from "react";
import { Search, X, Clock, Loader2 } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getSuggestions } from "../lib/api";
import { useAppStore } from "../lib/store";
import { motion, AnimatePresence } from "framer-motion";

export default function SearchBar({ size = "lg", autoFocus = false }) {
  const [searchParams] = useSearchParams();
  const urlQuery = searchParams.get("q") || "";

  const [query, setQuery] = useState(urlQuery);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [focused, setFocused] = useState(false);
  const inputRef = useRef(null);
  const debounceRef = useRef(null);
  const navigate = useNavigate();
  const { recentSearches, addRecentSearch, clearRecentSearches } = useAppStore();

  // Keep input in sync when URL changes (e.g. quick example buttons)
  useEffect(() => {
    setQuery(urlQuery);
  }, [urlQuery]);

  const fetchSuggestions = useCallback(async (q) => {
    if (q.length < 1) { setSuggestions([]); return; }
    setLoading(true);
    try {
      const data = await getSuggestions(q);
      setSuggestions(Array.isArray(data) ? data : []);
    } catch {
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchSuggestions(query), 250);
    return () => clearTimeout(debounceRef.current);
  }, [query, fetchSuggestions]);

  const handleSubmit = (q = query) => {
    const trimmed = q.trim();
    if (!trimmed) return;
    addRecentSearch(trimmed);
    setSuggestions([]);
    setFocused(false);
    navigate(`/?q=${encodeURIComponent(trimmed)}`);
  };

  const handleSelect = (formula) => {
    addRecentSearch(formula);
    setSuggestions([]);
    setFocused(false);
    navigate(`/material/${encodeURIComponent(formula)}`);
  };

  const handleClear = () => {
    setQuery("");
    setSuggestions([]);
    navigate("/");
    inputRef.current?.focus();
  };

  const isLg = size === "lg";

  return (
    <div className="relative w-full">
      {/* Input wrapper */}
      <div
        className={`flex items-center gap-3 bg-surface-700/60 border rounded-2xl transition-all duration-200 ${
          focused ? "border-primary-500 shadow-lg shadow-primary-500/20" : "border-white/10"
        } ${isLg ? "px-5 py-4" : "px-4 py-2.5"}`}
      >
        {loading ? (
          <Loader2 size={isLg ? 20 : 16} className="text-primary-400 animate-spin shrink-0" />
        ) : (
          <Search size={isLg ? 20 : 16} className="text-gray-400 shrink-0" />
        )}
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 150)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          placeholder="Search by formula, name, or element  (e.g. NaCl, Silicon, Fe)"
          autoFocus={autoFocus}
          className={`flex-1 bg-transparent outline-none text-gray-100 placeholder-gray-500 ${
            isLg ? "text-base" : "text-sm"
          }`}
          aria-label="Search materials"
        />
        {query && (
          <button onClick={handleClear}
            className="text-gray-500 hover:text-gray-300 transition-colors"
            aria-label="Clear search"
          >
            <X size={16} />
          </button>
        )}
        {isLg && (
          <button
            onClick={() => handleSubmit()}
            className="px-4 py-1.5 bg-primary-500 hover:bg-primary-600 text-white rounded-xl text-sm font-medium transition-colors shrink-0"
          >
            Search
          </button>
        )}
      </div>

      {/* Dropdown */}
      <AnimatePresence>
        {focused && (suggestions.length > 0 || (!query && recentSearches.length > 0)) && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full mt-2 left-0 right-0 z-50 bg-surface-800 border border-white/10 rounded-xl shadow-2xl overflow-hidden"
          >
            {suggestions.length > 0 && (
              <>
                <div className="px-3 pt-2 pb-1 text-xs text-gray-500 uppercase tracking-wide font-medium">
                  Suggestions
                </div>
                {suggestions.map((s) => (
                  <button
                    key={s.formula}
                    onMouseDown={() => handleSelect(s.formula)}
                    className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-primary-500/10 transition-colors text-left"
                  >
                    <Search size={14} className="text-primary-400 shrink-0" />
                    <span className="font-mono font-semibold text-sm text-gray-100">{s.formula}</span>
                    <span className="text-xs text-gray-400 truncate flex-1">{s.name || ""}</span>
                    {s.crystal_system && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-primary-500/10 text-primary-400 capitalize shrink-0">
                        {s.crystal_system}
                      </span>
                    )}
                  </button>
                ))}
              </>
            )}
            {!query && recentSearches.length > 0 && (
              <>
                <div className="px-3 pt-2 pb-1 flex justify-between items-center">
                  <span className="text-xs text-gray-500 uppercase tracking-wide">Recent</span>
                  <button onClick={clearRecentSearches} className="text-xs text-gray-500 hover:text-gray-300">Clear</button>
                </div>
                {recentSearches.map((s) => (
                  <button
                    key={s}
                    onMouseDown={() => handleSubmit(s)}
                    className="w-full flex items-center gap-3 px-4 py-2 hover:bg-white/5 transition-colors text-left"
                  >
                    <Clock size={14} className="text-gray-500 shrink-0" />
                    <span className="text-sm text-gray-300">{s}</span>
                  </button>
                ))}
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
