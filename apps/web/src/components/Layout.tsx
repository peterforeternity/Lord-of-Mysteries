import { Outlet, Link, useLocation } from "react-router-dom";
import MobileNav from "./MobileNav";

export default function Layout() {
  const location = useLocation();
  const hideNav = location.pathname === "/";

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-mystic-surface border-b border-mystic-card px-4 py-3 flex items-center justify-between shrink-0">
        <Link to="/" className="flex items-center gap-2 no-underline">
          <span className="text-mystic-gold text-xl font-serif font-bold tracking-wider">
            诡秘之主
          </span>
        </Link>
        <nav className="hidden md:flex items-center gap-4">
          {location.pathname !== "/" && (
            <>
              <Link
                to="/game"
                className="text-mystic-text-dim hover:text-mystic-gold text-sm transition-colors no-underline"
              >
                调查
              </Link>
              <Link
                to="/deduction"
                className="text-mystic-text-dim hover:text-mystic-gold text-sm transition-colors no-underline"
              >
                推理板
              </Link>
              <Link
                to="/save-load"
                className="text-mystic-text-dim hover:text-mystic-gold text-sm transition-colors no-underline"
              >
                存档
              </Link>
              <Link
                to="/settings"
                className="text-mystic-text-dim hover:text-mystic-gold text-sm transition-colors no-underline"
              >
                设置
              </Link>
            </>
          )}
        </nav>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        <Outlet />
      </main>

      {/* Mobile Bottom Nav */}
      {!hideNav && <MobileNav />}
    </div>
  );
}
