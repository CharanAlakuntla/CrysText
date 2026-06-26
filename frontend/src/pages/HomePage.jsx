import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Atom, Filter, ChevronLeft, ChevronRight, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import SearchBar from "../components/SearchBar";
import MaterialCard from "../components/MaterialCard";
import { SkeletonCard } from "../components/LoadingSpinner";
import { getMaterials, searchMaterials } from "../lib/api";
import { useAppStore } from "../lib/store";

const CRYSTAL_SYSTEMS = ["cubic", "hexagonal", "tetragonal", "orthorhombic", "monoclinic", "triclinic", "trigonal"];

const QUICK_EXAMPLES = [
  { label: "NaCl – Rock Salt", formula: "NaCl" },
  { label: "Si – Silicon", formula: "Si" },
  { label: "TiO2 – Rutile", formula: "TiO2" },
  { label: "GaAs – Semiconductor", formula: "GaAs" },
  { label: "SrTiO3 – Perovskite", formula: "SrTiO3" },
  { label: "CaF2 – Fluorite", formula: "CaF2" },
];

export default function HomePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [page, setPage] = useState(1);
  const [csFilter, setCsFilter] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const limit = 12;
  const { addRecentSearch } = useAppStore();

  const q = searchParams.get("q") || "";

  // Search or list
  const isSearching = q.length > 0;

  const { data: listData, isLoading: listLoading } = useQuery({
    queryKey: ["materials", page, csFilter],
    queryFn: () => getMaterials({ page, limit, crystal_system: csFilter || undefined }),
    enabled: !isSearching,
  });

  const { data: searchData, isLoading: searchLoading } = useQuery({
    queryKey: ["search", q, csFilter, page],
    queryFn: () =>
      searchMaterials({ query: q, limit, skip: (page - 1) * limit, crystal_system: csFilter || undefined }),
    enabled: isSearching,
    keepPreviousData: true,
  });

  useEffect(() => { setPage(1); }, [q]);

  const materials = isSearching ? searchData?.results : listData?.materials;
  const total = isSearching ? searchData?.total : listData?.total;
  const loading = isSearching ? searchLoading : listLoading;
  const totalPages = Math.ceil((total || 0) / limit);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Hero */}
      {!q && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <div className="inline-flex items-center gap-2 bg-primary-500/10 border border-primary-500/20 rounded-full px-4 py-1.5 text-xs text-primary-400 font-medium mb-4">
            <Atom size={12} />
            AI-Powered Materials Database
          </div>
          <h1 className="text-4xl md:text-5xl font-bold gradient-text mb-3">
            Explore Crystal Structures
          </h1>
          <p className="text-gray-400 text-lg max-w-xl mx-auto">
            Search thousands of materials by formula, name, or element.
            Get instant AI-powered scientific insights.
          </p>
        </motion.div>
      )}

      {/* Search bar */}
      <div className="max-w-2xl mx-auto mb-6">
        <SearchBar size="lg" />
      </div>

      {/* Quick examples */}
      {!q && (
        <div className="flex flex-wrap justify-center gap-2 mb-10">
          {QUICK_EXAMPLES.map((ex) => (
            <button
              key={ex.formula}
              onClick={() => {
                addRecentSearch(ex.formula);
                setSearchParams({ q: ex.formula });
              }}
              className="px-3 py-1.5 bg-surface-700/50 border border-white/8 rounded-xl text-xs text-gray-300 hover:border-primary-500/40 hover:text-primary-400 transition-colors"
            >
              {ex.label}
            </button>
          ))}
        </div>
      )}

      {/* Results header */}
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <div className="flex items-center gap-3">
          {q && (
            <div className="flex items-center gap-2">
              <span className="text-gray-300 font-medium">
                Results for <span className="text-primary-400 font-mono">"{q}"</span>
              </span>
              <button
                onClick={() => setSearchParams({})}
                className="p-1 rounded-lg hover:bg-white/5 text-gray-500 hover:text-gray-300 transition-colors"
              >
                <X size={14} />
              </button>
            </div>
          )}
          {total !== undefined && (
            <span className="text-sm text-gray-500">{total} material{total !== 1 ? "s" : ""}</span>
          )}
        </div>

        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-sm transition-colors ${
            showFilters || csFilter
              ? "border-primary-500/40 text-primary-400 bg-primary-500/10"
              : "border-white/10 text-gray-400 hover:border-white/20"
          }`}
        >
          <Filter size={14} />
          Filters{csFilter ? " (1)" : ""}
        </button>
      </div>

      {/* Filters */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-4 overflow-hidden"
          >
            <div className="bg-surface-700/40 border border-white/8 rounded-xl p-4">
              <div className="text-xs text-gray-400 uppercase mb-3 tracking-wide">Crystal System</div>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setCsFilter("")}
                  className={`px-3 py-1 rounded-lg text-xs transition-colors ${!csFilter ? "bg-primary-500 text-white" : "bg-white/5 text-gray-400 hover:bg-white/10"}`}
                >
                  All
                </button>
                {CRYSTAL_SYSTEMS.map((cs) => (
                  <button
                    key={cs}
                    onClick={() => setCsFilter(cs === csFilter ? "" : cs)}
                    className={`px-3 py-1 rounded-lg text-xs capitalize transition-colors ${csFilter === cs ? "bg-primary-500 text-white" : "bg-white/5 text-gray-400 hover:bg-white/10"}`}
                  >
                    {cs}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {[...Array(12)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : materials?.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <Atom size={48} className="mx-auto mb-4 opacity-20" />
          <p className="text-lg font-medium text-gray-400 mb-1">No materials found</p>
          <p className="text-sm">Try a different formula or element name</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {materials?.map((mat) => (
            <MaterialCard key={mat.formula || mat._id} material={mat} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center gap-3 mt-8">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="p-2 rounded-xl bg-surface-700/50 border border-white/8 disabled:opacity-30 hover:border-primary-500/40 transition-colors"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="text-sm text-gray-400">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="p-2 rounded-xl bg-surface-700/50 border border-white/8 disabled:opacity-30 hover:border-primary-500/40 transition-colors"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
