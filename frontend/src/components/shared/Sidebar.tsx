import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Sparkles,
  Building2,
  Clock,
  Users,
  Plus,
  ChevronDown,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Logo } from "./Logo";
import { Avatar } from "../ui/Avatar";
import { useAuth } from "@/hooks/useAuth";

const MAIN_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/ai-assistant", label: "AI assistant", icon: Sparkles },
];

const MANAGE_ITEMS = [
  { to: "/resources", label: "Resources", icon: Building2 },
  { to: "/availability", label: "Availability", icon: Clock },
  { to: "/users", label: "Users", icon: Users },
];

function NavGroupLabel({ children }: { children: string }) {
  return (
    <p className="mb-1.5 px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
      {children}
    </p>
  );
}

function SidebarLink({ to, label, icon: Icon }: { to: string; label: string; icon: typeof LayoutDashboard }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
          isActive ? "bg-brand-600 text-white font-medium" : "text-slate-300 hover:bg-white/5 hover:text-white"
        )
      }
    >
      <Icon className="h-[18px] w-[18px]" />
      {label}
    </NavLink>
  );
}

function initialsOf(name: string) {
  const parts = name.trim().split(/\s+/);
  return parts.length === 1 ? parts[0].slice(0, 2).toUpperCase() : (parts[0][0] + parts[1][0]).toUpperCase();
}

export function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  return (
    <div className="flex h-full flex-col p-4" onClick={onNavigate}>
      <div className="mb-6 px-1">
        <Logo light size={26} />
      </div>

      <button
        onClick={() => navigate("/ai-assistant")}
        className="mb-6 flex h-10 items-center justify-center gap-2 rounded-lg bg-brand-600 text-sm font-medium text-white hover:bg-brand-700 focus-ring"
      >
        <Plus className="h-4 w-4" /> New Meeting
      </button>

      <NavGroupLabel>Main</NavGroupLabel>
      <nav className="mb-6 flex flex-col gap-1">
        {MAIN_ITEMS.map((item) => (
          <SidebarLink key={item.to} {...item} />
        ))}
      </nav>

      <NavGroupLabel>Manage</NavGroupLabel>
      <nav className="flex flex-col gap-1">
        {MANAGE_ITEMS.map((item) => (
          <SidebarLink key={item.to} {...item} />
        ))}
      </nav>

      <div className="flex-1" />

      {user && (
        <button
          onClick={() => navigate("/settings")}
          className="flex items-center gap-2.5 rounded-lg border-t border-white/10 px-1 pt-4 text-left hover:opacity-90"
        >
          <Avatar initials={initialsOf(user.name)} size={30} colorClass="bg-white/10 text-white" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-white">{user.name}</p>
            <p className="text-xs text-slate-400">Settings</p>
          </div>
          <ChevronDown className="h-4 w-4 text-slate-400" />
        </button>
      )}

      <button
        onClick={() => {
          logout();
          navigate("/login");
        }}
        className="mt-1 flex items-center gap-2.5 rounded-lg px-1 py-2 text-sm text-slate-400 hover:text-white"
      >
        <LogOut className="h-4 w-4" /> Log out
      </button>
    </div>
  );
}

export function Sidebar({ className }: { className?: string }) {
  return (
    <aside className={cn("hidden w-[280px] shrink-0 bg-ink-950 md:block", className)}>
      <SidebarContent />
    </aside>
  );
}
