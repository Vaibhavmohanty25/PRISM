import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Upload,
  FolderKanban,
  Bot,
} from "lucide-react";

const navItems = [
  {
    label: "Dashboard",
    path: "/",
    icon: LayoutDashboard,
  },
  {
    label: "Upload Report",
    path: "/upload",
    icon: Upload,
  },
  {
    label: "Projects",
    path: "/projects",
    icon: FolderKanban,
  },
  {
    label: "PRISM Agent",
    path: "/agent",
    icon: Bot,
  },
];

export default function Sidebar() {
  return (
    <aside className="w-64 min-h-screen border-r border-slate-800 bg-slate-950 text-white">
      <div className="px-6 py-7 border-b border-slate-800">
        <h1 className="text-2xl font-bold tracking-tight">
          PRISM
        </h1>

        <p className="mt-1 text-xs text-slate-400">
          Construction Intelligence
        </p>
      </div>

      <nav className="p-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                [
                  "flex items-center gap-3 rounded-lg px-4 py-3 text-sm transition",
                  isActive
                    ? "bg-slate-800 text-white"
                    : "text-slate-400 hover:bg-slate-900 hover:text-white",
                ].join(" ")
              }
            >
              <Icon size={18} />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}