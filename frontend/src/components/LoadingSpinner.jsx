import { Atom } from "lucide-react";

export function LoadingSpinner({ text = "Loading..." }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-20">
      <div className="relative w-12 h-12">
        <div className="absolute inset-0 rounded-full border-2 border-primary-500/20 animate-ping" />
        <div className="absolute inset-0 rounded-full border-2 border-t-primary-500 border-transparent animate-spin" />
        <Atom size={20} className="absolute inset-0 m-auto text-primary-400" />
      </div>
      <p className="text-gray-400 text-sm animate-pulse">{text}</p>
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="bg-surface-700/30 border border-white/5 rounded-2xl p-5 animate-pulse">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-9 h-9 rounded-xl bg-white/5" />
        <div className="flex-1">
          <div className="h-4 bg-white/5 rounded w-24 mb-2" />
          <div className="h-3 bg-white/5 rounded w-36" />
        </div>
      </div>
      <div className="h-6 bg-white/5 rounded-lg w-28 mb-3" />
      <div className="grid grid-cols-2 gap-2">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-10 bg-white/5 rounded-lg" />
        ))}
      </div>
    </div>
  );
}
