import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Atom, Mail, Lock, Eye, EyeOff, UserPlus, Loader2, User } from "lucide-react";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { registerUser } from "../lib/api";
import { useAuthStore } from "../lib/authStore";

export default function RegisterPage() {
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "" });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const validate = () => {
    const e = {};
    if (!form.name.trim()) e.name = "Name is required";
    if (!form.email) e.email = "Email is required";
    else if (!/\S+@\S+\.\S+/.test(form.email)) e.email = "Enter a valid email";
    if (!form.password) e.password = "Password is required";
    else if (form.password.length < 6) e.password = "At least 6 characters";
    if (!form.confirm) e.confirm = "Please confirm your password";
    else if (form.password !== form.confirm) e.confirm = "Passwords don't match";
    return e;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setErrors({});
    setLoading(true);
    try {
      const data = await registerUser({ name: form.name.trim(), email: form.email, password: form.password });
      setAuth(data.user, data.token);
      toast.success(`Account created! Welcome, ${data.user.name}!`);
      navigate("/");
    } catch (err) {
      const msg = err?.response?.data?.detail || "Registration failed";
      toast.error(msg);
      setErrors({ general: msg });
    } finally {
      setLoading(false);
    }
  };

  const Field = ({ id, label, type = "text", value, onChange, placeholder, error, icon: Icon, extra }) => (
    <div>
      <label htmlFor={id} className="block text-sm text-gray-300 mb-1.5 font-medium">{label}</label>
      <div className={`flex items-center gap-3 bg-surface-800/80 border rounded-xl px-4 py-3 transition-colors ${
        error ? "border-red-500/50" : "border-white/10 focus-within:border-primary-500"
      }`}>
        <Icon size={16} className="text-gray-500 shrink-0" />
        <input
          id={id}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className="flex-1 bg-transparent outline-none text-gray-100 text-sm placeholder-gray-500"
        />
        {extra}
      </div>
      {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
    </div>
  );

  return (
    <div
      className="min-h-screen bg-surface-900 flex items-center justify-center px-4 py-8"
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
          <p className="text-gray-400 text-sm mt-2">Create your free account</p>
        </div>

        {/* Card */}
        <div className="bg-surface-700/50 border border-white/8 rounded-2xl p-8 shadow-2xl backdrop-blur-md">
          <h1 className="text-xl font-bold text-gray-100 mb-6">Get started</h1>

          {errors.general && (
            <div className="mb-4 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {errors.general}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
            <Field id="name" label="Full name" value={form.name} onChange={set("name")}
              placeholder="Jane Smith" error={errors.name} icon={User} />

            <Field id="email" label="Email address" type="email" value={form.email} onChange={set("email")}
              placeholder="you@example.com" error={errors.email} icon={Mail} />

            <Field
              id="password" label="Password" type={showPw ? "text" : "password"}
              value={form.password} onChange={set("password")}
              placeholder="Min. 6 characters" error={errors.password} icon={Lock}
              extra={
                <button type="button" onClick={() => setShowPw(!showPw)}
                  className="text-gray-500 hover:text-gray-300 transition-colors" aria-label="Toggle password">
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              }
            />

            <Field
              id="confirm" label="Confirm password" type={showPw ? "text" : "password"}
              value={form.confirm} onChange={set("confirm")}
              placeholder="Repeat your password" error={errors.confirm} icon={Lock}
            />

            {/* Password strength indicator */}
            {form.password && (
              <div className="flex gap-1.5">
                {[1, 2, 3, 4].map((i) => {
                  const strength = Math.min(4, Math.floor(form.password.length / 3));
                  const colors = ["bg-red-500", "bg-orange-500", "bg-yellow-500", "bg-emerald-500"];
                  return (
                    <div key={i} className={`h-1 flex-1 rounded-full transition-colors ${
                      i <= strength ? colors[strength - 1] : "bg-white/10"
                    }`} />
                  );
                })}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="mt-2 w-full flex items-center justify-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-colors shadow-lg shadow-primary-500/20"
            >
              {loading ? <Loader2 size={18} className="animate-spin" /> : <UserPlus size={18} />}
              {loading ? "Creating account..." : "Create Account"}
            </button>
          </form>

          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px bg-white/8" />
            <span className="text-xs text-gray-500">or</span>
            <div className="flex-1 h-px bg-white/8" />
          </div>

          <p className="text-center text-sm text-gray-400">
            Already have an account?{" "}
            <Link to="/login" className="text-primary-400 hover:text-primary-300 font-medium hover:underline">
              Sign in
            </Link>
          </p>
        </div>

        <p className="text-center mt-6 text-xs text-gray-500">
          <Link to="/" className="hover:text-gray-300 transition-colors">← Back to CrysText</Link>
        </p>
      </motion.div>
    </div>
  );
}
