import { useQuery } from "@tanstack/react-query";
import { GitCompare, X, Plus } from "lucide-react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { compareMaterials } from "../lib/api";
import { useAppStore } from "../lib/store";
import { LoadingSpinner } from "../components/LoadingSpinner";

const FIELDS = [
  { label: "Formula", key: "formula", mono: true },
  { label: "Name", key: "name" },
  { label: "Crystal System", key: "crystal_system" },
  { label: "Space Group", key: "space_group", mono: true },
  { label: "Density (g/cm³)", key: "density" },
  { label: "Band Gap (eV)", key: "band_gap" },
  { label: "Formation Energy", key: "formation_energy" },
  { label: "No. of Sites", key: "nsites" },
  { label: "Elements", key: (m) => m.elements?.join(", "), mono: true },
  { label: "a (Å)", key: (m) => m.lattice?.a },
  { label: "b (Å)", key: (m) => m.lattice?.b },
  { label: "c (Å)", key: (m) => m.lattice?.c },
  { label: "Volume (Å³)", key: (m) => m.lattice?.volume },
];

function getValue(mat, field) {
  if (typeof field.key === "function") return field.key(mat) ?? "—";
  return mat[field.key] ?? "—";
}

export default function ComparePage() {
  const { compareList, toggleCompare, clearCompare } = useAppStore();

  const { data, isLoading } = useQuery({
    queryKey: ["compare", compareList],
    queryFn: () => compareMaterials(compareList),
    enabled: compareList.length > 0,
  });

  const materials = data?.materials || [];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8 flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary-500/15 flex items-center justify-center">
            <GitCompare size={20} className="text-primary-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-100">Compare Materials</h1>
            <p className="text-gray-400 text-sm">Side-by-side property comparison (up to 4)</p>
          </div>
        </div>
        {compareList.length > 0 && (
          <button onClick={clearCompare} className="text-sm text-gray-400 hover:text-gray-200 flex items-center gap-1.5">
            <X size={14} /> Clear all
          </button>
        )}
      </div>

      {compareList.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <GitCompare size={48} className="mx-auto mb-4 opacity-20" />
          <p className="text-lg font-medium text-gray-400 mb-1">No materials selected</p>
          <p className="text-sm mb-6">Use the compare button on material cards to add materials here</p>
          <Link to="/" className="inline-flex items-center gap-2 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-xl text-sm transition-colors">
            <Plus size={16} /> Browse Materials
          </Link>
        </div>
      ) : isLoading ? (
        <LoadingSpinner text="Loading comparison..." />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px]">
            <thead>
              <tr>
                <th className="text-left p-3 text-xs uppercase text-gray-500 tracking-wide w-36">Property</th>
                {materials.map((m) => (
                  <th key={m.formula} className="p-3 text-center">
                    <div className="flex items-center justify-center gap-1.5 mb-1">
                      <span className="font-bold font-mono text-primary-400">{m.formula}</span>
                      <button
                        onClick={() => toggleCompare(m.formula)}
                        className="text-gray-500 hover:text-gray-300 transition-colors"
                        aria-label="Remove from compare"
                      >
                        <X size={13} />
                      </button>
                    </div>
                    <div className="text-xs text-gray-400 font-normal">{m.name}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {FIELDS.map((field) => (
                <tr key={field.label} className="border-t border-white/5">
                  <td className="p-3 text-sm text-gray-400 font-medium">{field.label}</td>
                  {materials.map((m) => {
                    const val = getValue(m, field);
                    return (
                      <td
                        key={m.formula}
                        className={`p-3 text-center text-sm ${field.mono ? "font-mono" : ""} text-gray-200`}
                      >
                        {val}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
