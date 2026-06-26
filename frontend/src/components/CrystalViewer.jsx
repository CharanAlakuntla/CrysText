/**
 * CrystalViewer – Three.js / React-Three-Fiber interactive 3D crystal viewer.
 * Renders atoms as spheres and infers bonds by distance.
 */
import { useRef, useMemo, Suspense } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Environment, Sphere, Cylinder, Html } from "@react-three/drei";
import * as THREE from "three";

// Element color palette (CPK-style)
const ELEMENT_COLORS = {
  H: "#ffffff", He: "#d9ffff", Li: "#cc80ff", Be: "#c2ff00",
  B: "#ffb5b5", C: "#909090", N: "#3050f8", O: "#ff0d0d",
  F: "#90e050", Na: "#ab5cf2", Mg: "#8aff00", Al: "#bfa6a6",
  Si: "#f0c8a0", P: "#ff8000", S: "#ffff30", Cl: "#1ff01f",
  K: "#8f40d4", Ca: "#3dff00", Ti: "#bfc2c7", Cr: "#8a99c7",
  Fe: "#e06633", Ni: "#50d050", Cu: "#c88033", Zn: "#7d80b0",
  Ga: "#c28f8f", Ge: "#668f8f", As: "#bd80e3", Se: "#ffa100",
  Br: "#a62929", Sr: "#00ff00", Y: "#94ffff", Zr: "#94e0e0",
  Nb: "#73c2c9", Mo: "#54b5b5", Ag: "#c0c0c0", Sn: "#668080",
  Sb: "#9e63b5", I: "#940094", Cs: "#57178f", Ba: "#00c900",
  La: "#70d4ff", W: "#2194d6", Au: "#ffd123", Pb: "#575961",
  Bi: "#9e4fb5", default: "#ff69b4",
};

// Covalent radii (Å) for atom display size
const COVALENT_RADII = {
  H: 0.31, C: 0.77, N: 0.75, O: 0.73, F: 0.71, S: 1.02,
  Cl: 0.99, Fe: 1.25, Cu: 1.28, Al: 1.43, Si: 1.17, Na: 1.66,
  K: 2.03, Ca: 1.97, Ti: 1.47, Cr: 1.28, Mn: 1.26, Ni: 1.24,
  Zn: 1.25, Ga: 1.22, Ge: 1.22, As: 1.19, Se: 1.16, Br: 1.14,
  default: 1.2,
};

function getColor(el) { return ELEMENT_COLORS[el] || ELEMENT_COLORS.default; }
function getRadius(el) { return (COVALENT_RADII[el] || COVALENT_RADII.default) * 0.4; }

// Convert fractional → Cartesian coordinates
function fracToCart(frac, lattice) {
  const [x, y, z] = frac;
  const a = lattice.a, b = lattice.b, c = lattice.c;
  const al = (lattice.alpha * Math.PI) / 180;
  const be = (lattice.beta * Math.PI) / 180;
  const ga = (lattice.gamma * Math.PI) / 180;

  const ax = a;
  const bx = b * Math.cos(ga);
  const by = b * Math.sin(ga);
  const cx = c * Math.cos(be);
  const cy = c * (Math.cos(al) - Math.cos(be) * Math.cos(ga)) / Math.sin(ga);
  const cz = Math.sqrt(Math.max(0, c * c - cx * cx - cy * cy));

  return [
    x * ax + y * bx + z * cx,
    x * 0  + y * by + z * cy,
    x * 0  + y * 0  + z * cz,
  ];
}

function Bond({ p1, p2, color }) {
  const mid = p1.map((v, i) => (v + p2[i]) / 2);
  const dx = p2[0] - p1[0], dy = p2[1] - p1[1], dz = p2[2] - p1[2];
  const len = Math.sqrt(dx * dx + dy * dy + dz * dz);
  const axis = new THREE.Vector3(0, 1, 0);
  const dir = new THREE.Vector3(dx, dy, dz).normalize();
  const quat = new THREE.Quaternion().setFromUnitVectors(axis, dir);

  return (
    <mesh position={mid} quaternion={quat}>
      <cylinderGeometry args={[0.05, 0.05, len, 8]} />
      <meshStandardMaterial color={color} roughness={0.4} metalness={0.2} />
    </mesh>
  );
}

function Crystal({ sites, lattice }) {
  const groupRef = useRef();

  // Compute Cartesian positions
  const atoms = useMemo(() => {
    if (!sites || !lattice) return [];
    return sites.map((s) => ({
      ...s,
      cart: fracToCart([s.x, s.y, s.z], lattice),
    }));
  }, [sites, lattice]);

  // Center
  const center = useMemo(() => {
    if (!atoms.length) return [0, 0, 0];
    const sum = atoms.reduce((acc, a) => [acc[0] + a.cart[0], acc[1] + a.cart[1], acc[2] + a.cart[2]], [0, 0, 0]);
    return sum.map((v) => v / atoms.length);
  }, [atoms]);

  // Bonds by distance threshold
  const bonds = useMemo(() => {
    const result = [];
    const threshold = 3.2; // Å
    for (let i = 0; i < atoms.length; i++) {
      for (let j = i + 1; j < atoms.length; j++) {
        const dx = atoms[i].cart[0] - atoms[j].cart[0];
        const dy = atoms[i].cart[1] - atoms[j].cart[1];
        const dz = atoms[i].cart[2] - atoms[j].cart[2];
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
        const maxBond = (getRadius(atoms[i].element) + getRadius(atoms[j].element)) / 0.4 * 1.15 + 0.4;
        if (dist < Math.min(threshold, maxBond)) {
          result.push({ i, j, dist });
        }
      }
    }
    return result;
  }, [atoms]);

  useFrame((_, delta) => {
    if (groupRef.current) groupRef.current.rotation.y += delta * 0.15;
  });

  if (!atoms.length) return null;

  return (
    <group ref={groupRef} position={center.map((v) => -v)}>
      {atoms.map((atom, idx) => (
        <mesh key={idx} position={atom.cart}>
          <sphereGeometry args={[getRadius(atom.element), 24, 24]} />
          <meshStandardMaterial
            color={getColor(atom.element)}
            roughness={0.25}
            metalness={0.15}
            envMapIntensity={0.8}
          />
        </mesh>
      ))}
      {bonds.map((b, idx) => (
        <Bond
          key={idx}
          p1={atoms[b.i].cart}
          p2={atoms[b.j].cart}
          color="#888"
        />
      ))}
    </group>
  );
}

export default function CrystalViewer({ material, height = "400px" }) {
  const sites = material?.sites;
  const lattice = material?.lattice;

  if (!sites || sites.length === 0 || !lattice) {
    return (
      <div
        style={{ height }}
        className="flex items-center justify-center bg-surface-900/60 rounded-2xl text-gray-500 text-sm"
      >
        No structure data available
      </div>
    );
  }

  return (
    <div style={{ height }} className="rounded-2xl overflow-hidden bg-surface-900/60 relative">
      <Canvas
        camera={{ position: [0, 0, 15], fov: 50 }}
        gl={{ antialias: true }}
        style={{ background: "transparent" }}
      >
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <directionalLight position={[-10, -5, -5]} intensity={0.3} color="#a5b4fc" />
        <pointLight position={[0, 0, 10]} intensity={0.5} color="#6366f1" />

        <Suspense fallback={null}>
          <Crystal sites={sites} lattice={lattice} />
          <Environment preset="city" />
        </Suspense>

        <OrbitControls enablePan enableZoom enableRotate makeDefault />
      </Canvas>

      {/* Legend */}
      <div className="absolute bottom-3 right-3 bg-surface-800/80 backdrop-blur border border-white/10 rounded-xl p-2 text-xs">
        <div className="flex flex-wrap gap-x-3 gap-y-1 max-w-[200px]">
          {[...new Set(sites.map((s) => s.element))].map((el) => (
            <div key={el} className="flex items-center gap-1.5">
              <div
                className="w-3 h-3 rounded-full"
                style={{ background: getColor(el) }}
              />
              <span className="text-gray-300">{el}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Controls hint */}
      <div className="absolute top-3 right-3 text-[10px] text-gray-600 bg-black/30 rounded-lg px-2 py-1">
        Drag · Scroll · Right-click
      </div>
    </div>
  );
}
