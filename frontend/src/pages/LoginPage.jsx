import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Atom, Mail, Lock, Eye, EyeOff, LogIn, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { loginUser } from "../lib/api";
import { useAuthStore } from "../lib/authStore";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const { setAuth } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from || "/";

  const validate = () => {
    const e = {};
    if (!email) e.email = "Email is required";
    else if (!/\S+@\S+\.\S+/.test(email)) e.email = "Enter a valid email";
    if (!password) e.password = "Password is required";
    return e;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setErrors({});
    setLoading(true);
    try {
      const data = await loginUser({ email, password });
      setAuth(data.user, data.token);
      toast.success(`Welcome back, ${data.user.name}!`);
      navigate(from, { replace: true });
    } catch (err) {
      const msg = err?.response?.data?.detail || "Login failed";
      toast.error(msg);
      setErrors({ general: msg });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface-900 flex items-center justify-center px-4"
      style={{
        backgroundImage:
          "radial-gradient(at 20% 30%, rgba(99,102,241,0.12) 0px, transparent 50%), radial-gradient(at 80% 70%, rgba(168,85,247,0.10) 0px, transparent 50%)",
      }}
    >
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-primary-500 flex items-center justify-center shadow-lg shadow-primary-500/30">
              <Atom size={20} className="text-white" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-white to-primary-400 bg-clip-text text-transparent">
              CrysText
            </span>
          </Link>
          <p className="text-gray-400 text-sm mt-2">Sign in to your account</p>
        </div>

        {/* Card */}
        <div className="bg-surface-700/50 border border-white/8 rounded-2xl p-8 shadow-2xl backdrop-blur-md">
          <h1 className="text-xl font-bold text-gray-100 mb-6">Welcome back</h1>

          {errors.general && (
            <div className="mb-4 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {errors.general}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
            {/* Email */}
            <div>
              <label className="block text-sm text-gray-300 mb-1.5 font-medium">
                Email address
              </label>
              <div className={`flex items-center gap-3 bg-surface-800/80 border rounded-xl px-4 py-3 transition-colors ${
                errors.email ? "border-red-500/50" : "border-white/10 focus-within:border-primary-500"
              }`}>
                <Mail size={16} className="text-gray-500 shrink-0" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="flex-1 bg-transparent outline-none text-gray-100 text-sm placeholder-gray-500"
                  autoComplete="email"
                  aria-label="Email"
                />
              </div>
              {errors.email && <p className="mt-1 text-xs text-red-400">{errors.email}</p>}
            </div>

            {/* Password */}
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="text-sm text-gray-300 font-medium">Password</label>
                <Link to="/forgot-password" className="text-xs text-primary-400 hover:underline">
                  Forgot password?
                </Link>
              </div>
              <div className={`flex items-center gap-3 bg-surface-800/80 border rounded-xl px-4 py-3 transition-colors ${
                errors.password ? "border-red-500/50" : "border-white/10 focus-within:border-primary-500"
              }`}>
                <Lock size={16} className="text-gray-500 shrink-0" />
                <input
                  type={showPw ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="flex-1 bg-transparent outline-none text-gray-100 text-sm placeholder-gray-500"
                  autoComplete="current-password"
                  aria-label="Password"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="text-gray-500 hover:text-gray-300 transition-colors"
                  aria-label={showPw ? "Hide password" : "Show password"}
                >
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.password && <p className="mt-1 text-xs text-red-400">{errors.password}</p>}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="mt-2 w-full flex items-center justify-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-colors shadow-lg shadow-primary-500/20"
            >
              {loading ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <LogIn size={18} />
              )}
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px bg-white/8" />
            <span className="text-xs text-gray-500">or</span>
            <div className="flex-1 h-px bg-white/8" />
          </div>

          <p className="text-center text-sm text-gray-400">
            Don't have an account?{" "}
            <Link to="/register" className="text-primary-400 hover:text-primary-300 font-medium hover:underline">
              Create one
            </Link>
          </p>
        </div>

        {/* Back to home */}
        <p className="text-center mt-6 text-xs text-gray-500">
          <Link to="/" className="hover:text-gray-300 transition-colors">
            ← Back to CrysText
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
