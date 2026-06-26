import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Heart, Trash2 } from "lucide-react";
import { motion } from "framer-motion";
import { getFavorites, removeFavorite } from "../lib/api";
import MaterialCard from "../components/MaterialCard";
import { LoadingSpinner } from "../components/LoadingSpinner";
import toast from "react-hot-toast";

export default function FavoritesPage() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["favorites"],
    queryFn: getFavorites,
  });

  const handleRemove = async (formula) => {
    await removeFavorite(formula);
    queryClient.invalidateQueries({ queryKey: ["favorites"] });
    toast("Removed from favorites");
  };

  const materials = data?.materials || [];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-red-500/15 flex items-center justify-center">
          <Heart size={20} className="text-red-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Favorites</h1>
          <p className="text-gray-400 text-sm">{materials.length} saved material{materials.length !== 1 ? "s" : ""}</p>
        </div>
      </div>

      {isLoading ? (
        <LoadingSpinner text="Loading favorites..." />
      ) : materials.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <Heart size={48} className="mx-auto mb-4 opacity-20" />
          <p className="text-lg font-medium text-gray-400 mb-1">No favorites yet</p>
          <p className="text-sm">Click the heart icon on any material to save it here</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {materials.map((mat) => (
            <div key={mat.formula} className="relative group">
              <MaterialCard material={mat} showCompare />
              <button
                onClick={() => handleRemove(mat.formula)}
                className="absolute top-3 right-3 p-1.5 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20 opacity-0 group-hover:opacity-100 transition-opacity"
                aria-label="Remove from favorites"
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
