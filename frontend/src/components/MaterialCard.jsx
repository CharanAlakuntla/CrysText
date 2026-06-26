import { Link } from "react-router-dom";
import { Atom, Layers, GitCompare, Heart } from "lucide-react";
import { motion } from "framer-motion";
import { useAppStore } from "../lib/store";
import { addFavorite, removeFavorite } from "../lib/api";
import { useState } from "react";
import toast from "react-hot-toast";

const CRYSTAL_COLORS = {
  cubic: "text-blue-400 bg-blue-400/10",
  hexagonal: "text-purple-400 bg-purple-400/10",
  tetragonal: "text-emerald-400 bg-emerald-400/10",
  orthorhombic: "text-orange-400 bg-orange-400/10",
  monoclinic: "text-pink-400 bg-pink-400/10",
  triclinic: "text-yellow-400 bg-yellow-400/10",
  trigonal: "text-cyan-400 bg-cyan-400/10",
};

export default function MaterialCard({ material, showCompare = true }) {
  const { compareList, toggleCompare } = useAppStore();
  const [favorited, setFavorited] = useState(false);

  const isInCompare = compareList.includes(material.formula);
  const csKey = (material.crystal_system || "").toLowerCase();
  const csStyle = CRYSTAL_COLORS[csKey] || "text-gray-400 bg-white/5";

  const handleFavorite = async (e) => {
    e.preventDefault();
    try {
      if (favorited) {
        await removeFavorite(material.formula);
        toast("Removed from favorites");
      } else {
        await addFavorite(material.formula);
        toast.success("Added to favorites");
      }
      setFavorited(!favorited);
    } catch {
      toast.error("Failed to update favorites");
    }
  };

  const handleCompare = (e) => {
    e.preventDefault();
    if (!isInCompare && compareList.length >= 4) {
      toast.error("Max 4 materials for comparison");
      return;
    }
    toggleCompare(material.formula);
    toast(isInCompare ? "Removed from compare" : "Added to compare");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      transition={{ duration: 0.2 }}
    >
      <Link
        to={`/material/${material.formula}`}
        className="block bg-surface-700/50 border border-white/8 rounded-2xl p-5 hover:border-primary-500/40 hover:shadow-lg hover:shadow-primary-500/10 transition-all duration-200"
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-primary-500/15 flex items-center justify-center">
              <Atom size={18} className="text-primary-400" />
            </div>
            <div>
              <div className="font-bold text-base text-gray-100 font-mono">{material.formula}</div>
              <div className="text-xs text-gray-400 truncate max-w-[160px]">{material.name}</div>
            </div>
          </div>
          <div className="flex items-center gap-1">
            {showCompare && (
              <button
                onClick={handleCompare}
                className={`p-1.5 rounded-lg transition-colors ${
                  isInCompare ? "text-primary-400 bg-primary-400/10" : "text-gray-500 hover:text-gray-300 hover:bg-white/5"
                }`}
                aria-label="Add to compare"
              >
                <GitCompare size={14} />
              </button>
            )}
            <button
              onClick={handleFavorite}
              className={`p-1.5 rounded-lg transition-colors ${
                favorited ? "text-red-400 bg-red-400/10" : "text-gray-500 hover:text-gray-300 hover:bg-white/5"
              }`}
              aria-label="Favorite"
            >
              <Heart size={14} fill={favorited ? "currentColor" : "none"} />
            </button>
          </div>
        </div>

        {/* Crystal system badge */}
        {material.crystal_system && (
          <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium mb-3 ${csStyle}`}>
            <Layers size={11} />
            {material.crystal_system}
          </div>
        )}

        {/* Properties grid */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          {[
            ["Space Group", material.space_group],
            ["Density", material.density ? `${material.density} g/cm³` : null],
            ["Band Gap", material.band_gap != null ? `${material.band_gap} eV` : null],
            ["Sites", material.nsites],
          ].map(([label, val]) =>
            val ? (
              <div key={label} className="bg-surface-800/60 rounded-lg px-2.5 py-1.5">
                <div className="text-gray-500 mb-0.5">{label}</div>
                <div className="font-medium text-gray-200 truncate">{val}</div>
              </div>
            ) : null
          )}
        </div>

        {/* Tags */}
        {material.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {material.tags.slice(0, 3).map((tag) => (
              <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-gray-400 capitalize">
                {tag}
              </span>
            ))}
          </div>
        )}
      </Link>
    </motion.div>
  );
}
