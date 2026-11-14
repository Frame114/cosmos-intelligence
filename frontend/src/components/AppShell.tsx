import {
  Activity,
  Atom,
  BookmarkCheck,
  ChevronDown,
  CircleHelp,
  Globe2,
  Menu,
  Orbit,
  Search,
  Settings2,
  Sparkles,
  Telescope,
  X,
} from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useApiQuery } from "../hooks/useApiQuery";
import type { HealthResponse } from "../types";

const primaryNavigation = [
  { to: "/overview", label: "Overview", icon: Orbit },
  { to: "/astronomy", label: "Astronomy", icon: Telescope },
  { to: "/asteroids", label: "Asteroids", icon: Atom },
  { to: "/space-weather", label: "Space weather", icon: Activity },
  { to: "/earth-events", label: "Earth events", icon: Globe2 },
  { to: "/media", label: "NASA media", icon: Sparkles },
];

const workspaceNavigation = [
  { to: "/assistant", label: "Research assistant", icon: Sparkles },
  { to: "/reports", label: "Reports", icon: ChevronDown },
  { to: "/saved", label: "Saved records", icon: BookmarkCheck },
  { to: "/settings", label: "Settings", icon: Settings2 },
];

export function AppShell() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [search, setSearch] = useState("");
  const navigate = useNavigate();
  const apiHealth = useApiQuery<HealthResponse>("/health/live");

  useEffect(() => {
    if (!menuOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMenuOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [menuOpen]);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = search.trim();
    if (!value) return;
    navigate(`/astronomy?q=${encodeURIComponent(value)}`);
    setSearch("");
    setMenuOpen(false);
  }

  function closeMenu() {
    setMenuOpen(false);
  }

  const healthLabel = apiHealth.error
    ? "API unavailable"
    : apiHealth.pending
      ? "Checking API"
      : apiHealth.data?.status === "ok"
        ? "API online"
        : "API status unknown";

  return (
    <div className="shell-grid">
      {menuOpen && <button aria-label="Close navigation" className="mobile-scrim" onClick={closeMenu} />}
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`} aria-label="Application navigation">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true"><Orbit size={23} strokeWidth={1.7} /></div>
          <div className="brand-copy">
            <span className="brand-name">COSMOS</span>
            <span className="brand-subtitle">INTELLIGENCE</span>
          </div>
          <button className="icon-button sidebar-close" aria-label="Close navigation" onClick={closeMenu}>
            <X size={19} />
          </button>
        </div>

        <div className="workspace-switcher">
          <div className="workspace-symbol">CI</div>
          <div className="workspace-copy"><span>Research workspace</span><small>Public data</small></div>
          <ChevronDown size={15} aria-hidden="true" />
        </div>

        <nav className="primary-nav" aria-label="Primary">
          <p className="nav-section-label">EXPLORE</p>
          {primaryNavigation.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => `nav-link ${isActive ? "nav-link-active" : ""}`}
              onClick={closeMenu}
            >
              <Icon size={17} strokeWidth={1.8} aria-hidden="true" />
              <span>{label}</span>
            </NavLink>
          ))}
          <p className="nav-section-label nav-section-spaced">WORKSPACE</p>
          {workspaceNavigation.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => `nav-link ${isActive ? "nav-link-active" : ""}`}
              onClick={closeMenu}
            >
              <Icon size={17} strokeWidth={1.8} aria-hidden="true" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className={`connection-row ${apiHealth.error ? "connection-error" : ""}`}>
            <span className="connection-dot" aria-hidden="true" />
            <span>{healthLabel}</span>
            <span className="connection-label">LIVE</span>
          </div>
          <a className="sidebar-help" href="https://api.nasa.gov/" target="_blank" rel="noreferrer">
            <CircleHelp size={16} aria-hidden="true" />
            <span>Data sources</span>
          </a>
          <div className="sidebar-version"><span>Independent research tool</span><span>v0.1</span></div>
        </div>
      </aside>

      <div className="main-column">
        <header className="topbar">
          <button
            className="icon-button mobile-menu-button"
            aria-label="Open navigation"
            aria-expanded={menuOpen}
            aria-controls="primary-navigation"
            onClick={() => setMenuOpen(true)}
          >
            <Menu size={21} />
          </button>
          <div className="breadcrumb"><span>Mission control</span><span className="breadcrumb-divider">/</span><strong>Research workspace</strong></div>
          <form className="global-search" role="search" onSubmit={submitSearch}>
            <Search size={16} aria-hidden="true" />
            <label className="sr-only" htmlFor="global-search-input">Search astronomy records</label>
            <input
              id="global-search-input"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search the cosmos..."
              type="search"
            />
            <kbd>⌘ K</kbd>
          </form>
          <div className="topbar-actions">
            <div className="utc-clock"><span className="status-dot" aria-hidden="true" />UTC <time>{new Date().toISOString().slice(11, 16)}</time></div>
            <div className="avatar" title="Public workspace">CI</div>
          </div>
        </header>
        <main id="main-content" className="main-content" tabIndex={-1}>
          <Outlet />
        </main>
        <footer className="site-footer">
          <span>Cosmos Intelligence is an independent research project and is not affiliated with NASA.</span>
          <a href="https://www.nasa.gov/nasa-brand-center/images-and-media/" target="_blank" rel="noreferrer">NASA media guidance</a>
        </footer>
      </div>
    </div>
  );
}
