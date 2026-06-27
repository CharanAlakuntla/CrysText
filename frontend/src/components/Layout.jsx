import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { Atom, BarChart3, Heart, GitCompare, Moon, Sun, Menu, X, LogIn, LogOut, User } from "lucide-react";
import { useState } from "react";
import { useAppStore } from "../lib/store";
import { useAuthStore } from "../lib/authStore";
import toast from "react-hot-toast";
import clsx from "clsx";

const navItems = [
  { to: "/", label: "Search", icon: Atom },
  { to: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { to: "/favorites", label: "Favorites", icon: Heart },
  { to: "/compare", label: "Compare", icon: GitCompare },
];

export default function Layout() {
  const { darkMode, toggleDarkMode } = useAppStore();
  const { user, logout } = useAuthStore();
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();

  // Sync dark mode to html element on mount and change
  const applyDarkMode = (dark) => {
    if (dark) document.documentElement.classList.add("dark");
    else document.documentElement.classList.remove("dark");
  };

  // Apply on mount
  useState(() => { applyDarkMode(darkMode); });

  const handleToggleDark = () => {
    toggleDarkMode();
    applyDarkMode(!darkMode);
  };

  const handleLogout = () => {
    logout();
    toast("Signed out");
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-surface-900 text-gray-100">
      {/* Top Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 h-14 bg-surface-800/80 backdrop-blur-md border-b border-white/8 flex items-center px-4 gap-4">
        {/* Logo */}
        <NavLink to="/" className="flex items-center gap-2 mr-4 shrink-0">
          <div className="w-7 h-7 rounded-lg bg-primary-500 flex items-center justify-center shadow-lg shadow-primary-500/30">
            <Atom size={16} className="text-white" />
          </div>
          <span className="font-bold text-lg gradient-text hidden sm:block">CrysText</span>
        </NavLink>

        {/* Desktop nav links */}
        <div className="hidden md:flex items-center gap-1 flex-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary-500/20 text-primary-400"
                    : "text-gray-400 hover:text-gray-100 hover:bg-white/5"
                )
              }
            >
              <Icon size={15} />
              {label}
            </NavLink>
          ))}
        </div>

        <div className="flex items-center gap-2 ml-auto">
          <button
            onClick={handleToggleDark}
            className="p-2 rounded-lg text-gray-400 hover:text-gray-100 hover:bg-white/5 transition-colors"
            aria-label="Toggle dark mode"
          >
            {darkMode ? <Sun size={16} /> : <Moon size={16} />}
          </button>

          {user ? (
            <div className="flex items-center gap-2">
              <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-primary-500/10 border border-primary-500/20">
                <User size={14} className="text-primary-400" />
                <span className="text-sm text-primary-400 font-medium">{user.name}</span>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-gray-400 hover:text-gray-100 hover:bg-white/5 text-sm transition-colors"
              >
                <LogOut size={15} />
                <span className="hidden sm:inline">Sign out</span>
              </button>
            </div>
          ) : (
            <NavLink
              to="/login"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-primary-500 hover:bg-primary-600 text-white text-sm font-medium transition-colors"
            >
              <LogIn size={15} />
              Sign in
            </NavLink>
          )}

          {/* Mobile menu */}
          <button
            className="md:hidden p-2 rounded-lg text-gray-400 hover:bg-white/5"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            {menuOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </nav>

      {/* Mobile drawer */}
      {menuOpen && (
        <div className="md:hidden fixed top-14 left-0 right-0 z-40 bg-surface-800 border-b border-white/8 p-4 flex flex-col gap-2">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              onClick={() => setMenuOpen(false)}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium",
                  isActive ? "bg-primary-500/20 text-primary-400" : "text-gray-300 hover:bg-white/5"
                )
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </div>
      )}

      {/* Page content */}
      <main className="pt-14 min-h-screen">
        <Outlet />
      </main>
    </div>
  );
}
