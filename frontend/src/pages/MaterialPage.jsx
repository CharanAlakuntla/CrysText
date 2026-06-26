import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  ArrowLeft, Download, FileText, Heart, GitCompare,
  Atom, Layers, Zap, Box, Info, Sparkles, ChevronDown, ChevronUp
} from "lucide-react";
import { useState } from "react";
import toast from "react-hot-toast";
import CrystalViewer from "../components/CrystalViewer";
import MaterialCard from "../components/MaterialCard";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { getMaterial, getSimilar, addFavorite, removeFavorite, getCifDownloadUrl, getPdfDownloadUrl } from "../lib/api";
import { useAppStore } from "../lib/store";

function PropRow({ label, value, mono = false }) {
  if (value == null || value === "") return null;
  return (
    <div className="flex justify-between items-start gap-4 py-2.5 border-b border-white/5 last:border-0">
      <span className="text-gray-400 text-sm shrink-0">{label}</span>
      <span className={`text-gray-100 text-sm text-right ${mono ? "font-mono" : "font-medium"}`}>{value}</span>
    </div>
  );
}

function Section({ title, icon: Icon, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="bg-surface-700/40 border border-white/8 rounded-2xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-2 font-semibold text-sm text-gray-200">
          <Icon size={16} className="text-primary-400" />
          {title}
        </div>
        {open ? <ChevronUp size={16} className="text-gray-500" /> : <ChevronDown size={16} className="text-gray-500" />}
      </button>
      {open && <div className="px-5 pb-5">{children}</div>}
    </div>
  );
}

export default function MaterialPage() {
  const { formula } = useParams();
  const { compareList, toggleCompare } = useAppStore();
  const [favorited, setFavorited] = useState(false);
  const [showAllSites, setShowAllSites] = useState(false);

  const { data: material, isLoading, isError } = useQuery({
    queryKey: ["material", formula],
    queryFn: () => getMaterial(formula),
  });

  const { data: similarData } = useQuery({
    queryKey: ["similar", formula],
    queryFn: () => getSimilar(formula),
    enabled: !!formula,
  });

  const handleFavorite = async () => {
    try {
      if (favorited) { await removeFavorite(formula); toast("Removed from favorites"); }
      else { await addFavorite(formula); toast.success("Added to favorites"); }
      setFavorited(!favorited);
    } catch { toast.error("Failed"); }
  };

  const handleCompare = () => {
    const inList = compareList.includes(formula);
    if (!inList && compareList.length >= 4) { toast.error("Max 4 materials"); return; }
    toggleCompare(formula);
    toast(inList ? "Removed from compare" : "Added to compare");
  };

  if (isLoading) return <div className="max-w-7xl mx-auto px-4 py-8"><LoadingSpinner text="Loading material..." /></div>;
  if (isError || !material) return (
    <div className="max-w-7xl mx-auto px-4 py-20 text-center">
      <p className="text-gray-400 text-lg">Material not found: <span className="font-mono text-primary-400">{formula}</span></p>
      <Link to="/" className="mt-4 inline-flex items-center gap-2 text-primary-400 hover:underline"><ArrowLeft size={16} /> Back to search</Link>
    </div>
  );

  const lat = material.lattice;
  const sitesToShow = showAllSites ? material.sites : material.sites?.slice(0, 8);

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Back */}
      <Link to="/" className="inline-flex items-center gap-2 text-gray-400 hover:text-gray-100 text-sm mb-6 transition-colors">
        <ArrowLeft size={16} /> Back to search
      </Link>

      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-3xl font-bold font-mono text-white">{material.formula}</h1>
              {material.crystal_system && (
                <span className="px-2.5 py-1 text-xs font-medium rounded-lg bg-primary-500/15 text-primary-400 border border-primary-500/20 capitalize">
                  {material.crystal_system}
                </span>
              )}
            </div>
            <p className="text-gray-400 text-lg">{material.name}</p>
            {material.tags?.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {material.tags.map((t) => (
                  <span key={t} className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-gray-400 capitalize">{t}</span>
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 flex-wrap">
            <button onClick={handleFavorite}
              className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-sm transition-colors ${favorited ? "border-red-500/40 text-red-400 bg-red-500/10" : "border-white/10 text-gray-400 hover:border-white/20"}`}>
              <Heart size={15} fill={favorited ? "currentColor" : "none"} /> Favorite
            </button>
            <button onClick={handleCompare}
              className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-sm transition-colors ${compareList.includes(formula) ? "border-primary-500/40 text-primary-400 bg-primary-500/10" : "border-white/10 text-gray-400 hover:border-white/20"}`}>
              <GitCompare size={15} /> Compare
            </button>
            <a href={getCifDownloadUrl(formula)} download
              className="flex items-center gap-2 px-3 py-2 rounded-xl border border-white/10 text-gray-400 hover:border-white/20 text-sm transition-colors">
              <Download size={15} /> CIF
            </a>
            <a href={getPdfDownloadUrl(formula)} download
              className="flex items-center gap-2 px-3 py-2 rounded-xl bg-primary-500 hover:bg-primary-600 text-white text-sm transition-colors">
              <FileText size={15} /> PDF Report
            </a>
          </div>
        </div>
      </motion.div>

      {/* Main grid */}
      <div className="grid lg:grid-cols-5 gap-6">
        {/* Left column – properties */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <Section title="Basic Properties" icon={Atom}>
            <PropRow label="Formula" value={material.formula} mono />
            <PropRow label="Name" value={material.name} />
            <PropRow label="Crystal System" value={material.crystal_system} />
            <PropRow label="Space Group" value={`${material.space_group} (${material.space_group_number})`} mono />
            <PropRow label="No. of Sites" value={material.nsites} />
            <PropRow label="Elements" value={material.elements?.join(", ")} mono />
          </Section>

          <Section title="Thermodynamic" icon={Zap}>
            <PropRow label="Density" value={material.density != null ? `${material.density} g/cm³` : null} />
            <PropRow label="Band Gap" value={material.band_gap != null ? `${material.band_gap} eV` : null} />
            <PropRow label="Formation Energy" value={material.formation_energy != null ? `${material.formation_energy} eV/atom` : null} />
          </Section>

          {lat && (
            <Section title="Lattice Parameters" icon={Box}>
              <PropRow label="a (Å)" value={lat.a} mono />
              <PropRow label="b (Å)" value={lat.b} mono />
              <PropRow label="c (Å)" value={lat.c} mono />
              <PropRow label="α (°)" value={lat.alpha} mono />
              <PropRow label="β (°)" value={lat.beta} mono />
              <PropRow label="γ (°)" value={lat.gamma} mono />
              <PropRow label="Volume (Å³)" value={lat.volume} mono />
            </Section>
          )}
        </div>

        {/* Right column – viewer + AI */}
        <div className="lg:col-span-3 flex flex-col gap-4">
          {/* 3D Viewer */}
          <div className="bg-surface-700/40 border border-white/8 rounded-2xl overflow-hidden">
            <div className="flex items-center gap-2 px-5 py-3 border-b border-white/8">
              <Layers size={16} className="text-purple-400" />
              <span className="font-semibold text-sm text-gray-200">3D Crystal Structure</span>
            </div>
            <div className="p-3">
              <CrystalViewer material={material} height="350px" />
            </div>
          </div>

          {/* AI Summary */}
          {material.ai_summary && (
            <Section title="AI Material Summary" icon={Sparkles}>
              <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-line">
                {material.ai_summary}
              </div>
            </Section>
          )}

          {/* Atomic sites */}
          {material.sites?.length > 0 && (
            <Section title="Atomic Coordinates" icon={Info} defaultOpen={false}>
              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono">
                  <thead>
                    <tr className="text-gray-500">
                      <th className="text-left pb-2 pr-4">Label</th>
                      <th className="text-left pb-2 pr-4">Element</th>
                      <th className="text-right pb-2 pr-4">x</th>
                      <th className="text-right pb-2 pr-4">y</th>
                      <th className="text-right pb-2">z</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sitesToShow?.map((site, i) => (
                      <tr key={i} className="border-t border-white/5">
                        <td className="py-1.5 pr-4 text-gray-300">{site.label}</td>
                        <td className="pr-4 text-primary-400">{site.element}</td>
                        <td className="text-right pr-4 text-gray-300">{site.x?.toFixed(5)}</td>
                        <td className="text-right pr-4 text-gray-300">{site.y?.toFixed(5)}</td>
                        <td className="text-right text-gray-300">{site.z?.toFixed(5)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {material.sites?.length > 8 && (
                  <button
                    onClick={() => setShowAllSites(!showAllSites)}
                    className="mt-3 text-xs text-primary-400 hover:underline"
                  >
                    {showAllSites ? "Show less" : `Show all ${material.sites.length} sites`}
                  </button>
                )}
              </div>
            </Section>
          )}
        </div>
      </div>

      {/* Similar materials */}
      {similarData?.materials?.length > 0 && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-200 mb-4">Similar Materials</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {similarData.materials.map((m) => <MaterialCard key={m.formula} material={m} />)}
          </div>
        </div>
      )}
    </div>
  );
}
