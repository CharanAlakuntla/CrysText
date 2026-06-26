import { useQuery } from "@tanstack/react-query";
import { BarChart3, Atom, Layers, Database, TrendingUp } from "lucide-react";
import { motion } from "framer-motion";
import { getStats, getMaterials } from "../lib/api";
import { LoadingSpinner } from "../components/LoadingSpinner";
import MaterialCard from "../components/MaterialCard";

const COLORS = ["#6366f1", "#8b5cf6", "#a855f7", "#ec4899", "#06b6d4", "#10b981", "#f59e0b"];

function StatCard({ label, value, icon: Icon, color = "primary" }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-surface-700/40 border border-white/8 rounded-2xl p-5 flex items-center gap-4"
    >
      <div className={`w-11 h-11 rounded-xl bg-primary-500/15 flex items-center justify-center shrink-0`}>
        <Icon size={22} className="text-primary-400" />
      </div>
      <div>
        <div className="text-2xl font-bold text-gray-100">{value ?? "—"}</div>
        <div className="text-sm text-gray-400">{label}</div>
      </div>
    </motion.div>
  );
}

function CrystalSystemBar({ name, count, max, colorIdx }) {
  const pct = max > 0 ? (count / max) * 100 : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-gray-400 w-28 capitalize shrink-0">{name || "Unknown"}</span>
      <div className="flex-1 bg-white/5 rounded-full h-2">
        <div
          className="h-2 rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: COLORS[colorIdx % COLORS.length] }}
        />
      </div>
      <span className="text-xs text-gray-300 w-8 text-right">{count}</span>
    </div>
  );
}

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({ queryKey: ["stats"], queryFn: getStats });
  const { data: latestData } = useQuery({
    queryKey: ["latest-materials"],
    queryFn: () => getMaterials({ page: 1, limit: 4 }),
  });

  if (isLoading) return <div className="max-w-7xl mx-auto px-4 py-8"><LoadingSpinner text="Loading dashboard..." /></div>;

  const csEntries = Object.entries(stats?.crystal_system_distribution || {}).sort((a, b) => b[1] - a[1]);
  const maxCount = csEntries[0]?.[1] || 1;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-primary-500/15 flex items-center justify-center">
          <BarChart3 size={20} className="text-primary-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Dashboard</h1>
          <p className="text-gray-400 text-sm">Database overview and statistics</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Materials" value={stats?.total_materials?.toLocaleString()} icon={Database} />
        <StatCard label="Crystal Systems" value={csEntries.length} icon={Layers} />
        <StatCard label="Unique Elements" value="—" icon={Atom} />
        <StatCard label="With AI Summary" value={stats?.total_materials?.toLocaleString()} icon={TrendingUp} />
      </div>

      {/* Charts row */}
      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        {/* Crystal system distribution */}
        <div className="bg-surface-700/40 border border-white/8 rounded-2xl p-6">
          <h2 className="font-semibold text-gray-200 mb-5 flex items-center gap-2">
            <Layers size={16} className="text-primary-400" />
            Crystal System Distribution
          </h2>
          {csEntries.length === 0 ? (
            <p className="text-gray-500 text-sm">No data yet — run the ingest script first.</p>
          ) : (
            <div className="flex flex-col gap-3">
              {csEntries.map(([name, count], i) => (
                <CrystalSystemBar key={name} name={name} count={count} max={maxCount} colorIdx={i} />
              ))}
            </div>
          )}
        </div>

        {/* Quick info */}
        <div className="bg-surface-700/40 border border-white/8 rounded-2xl p-6">
          <h2 className="font-semibold text-gray-200 mb-5 flex items-center gap-2">
            <TrendingUp size={16} className="text-primary-400" />
            Database Info
          </h2>
          <div className="flex flex-col gap-3 text-sm">
            {[
              ["Backend", "FastAPI + MongoDB"],
              ["AI Engine", "Ollama (Mistral / Llama 3)"],
              ["Structure Parser", "pymatgen"],
              ["3D Viewer", "Three.js / R3F"],
              ["Frontend", "React 18 + Tailwind CSS"],
              ["Dataset", "CIF files (auto-indexed)"],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between border-b border-white/5 pb-2 last:border-0">
                <span className="text-gray-400">{k}</span>
                <span className="text-gray-200 font-medium">{v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Latest materials */}
      {latestData?.materials?.length > 0 && (
        <div>
          <h2 className="font-semibold text-gray-200 mb-4 flex items-center gap-2">
            <Atom size={16} className="text-primary-400" />
            Materials in Database
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {latestData.materials.map((m) => <MaterialCard key={m.formula} material={m} />)}
          </div>
        </div>
      )}
    </div>
  );
}
