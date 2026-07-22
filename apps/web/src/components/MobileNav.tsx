import { Link, useLocation } from "react-router-dom";

const navItems = [
  { path: "/game", label: "调查", icon: "🔍" },
  { path: "/deduction", label: "推理板", icon: "🧩" },
  { path: "/ritual", label: "仪式", icon: "🔮" },
  { path: "/save-load", label: "存档", icon: "💾" },
  { path: "/settings", label: "设置", icon: "⚙️" },
];

export default function MobileNav() {
  const location = useLocation();

  return (
    <nav className="md:hidden bg-mystic-surface border-t border-mystic-card mobile-nav-safe">
      <div className="flex items-center justify-around py-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg transition-colors no-underline ${
                isActive
                  ? "text-mystic-gold"
                  : "text-mystic-text-dim hover:text-mystic-text"
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              <span className="text-[10px]">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
