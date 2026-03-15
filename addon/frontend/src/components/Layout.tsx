import { NavLink, Outlet } from 'react-router-dom';
import { Trophy, Home, Volume2, VolumeX } from 'lucide-react';
import { useState } from 'react';
import { toggleMute } from '../api/client';

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/' },
  { label: 'Teams', path: '/teams' },
  { label: 'Games', path: '/games' },
  { label: 'Sound Library', path: '/sounds' },
  { label: 'Settings', path: '/settings' },
];

export default function Layout() {
  const [muted, setMuted] = useState(false);

  const handleMuteToggle = async () => {
    try {
      const res = await toggleMute();
      setMuted(res.muted);
    } catch { /* ignore */ }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b-4 border-navy bg-cream sticky top-0 z-50">
        <div className="max-w-[1920px] mx-auto px-6 py-4 flex justify-between items-center">
          <NavLink to="/" className="flex items-center gap-4">
            <div className="w-12 h-12 border-2 border-navy bg-accent flex items-center justify-center">
              <Trophy className="w-6 h-6 text-cream" />
            </div>
            <div>
              <h1 className="font-rokkitt text-2xl font-bold text-navy tracking-wide uppercase leading-none">
                GameSync
              </h1>
              <p className="font-archivo text-xs text-muted uppercase tracking-widest">
                Heritage Playbook v1.0
              </p>
            </div>
          </NavLink>

          <nav className="hidden md:flex gap-8">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  isActive ? 'nav-link-active' : 'nav-link'
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <button
              onClick={handleMuteToggle}
              className="w-10 h-10 border-2 border-navy flex items-center justify-center hover:bg-navy hover:text-cream transition-colors"
              title={muted ? 'Unmute' : 'Mute'}
            >
              {muted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
            </button>
            <div className="flex items-center gap-2 px-3 py-1 border-2 border-navy bg-cream">
              <div className="w-2 h-2 rounded-full bg-green-status" />
              <span className="font-archivo text-xs font-bold text-navy uppercase">
                Connected
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* HA Integration Bar */}
      <div className="border-b-2 border-navy bg-navy text-cream">
        <div className="max-w-[1920px] mx-auto px-6 py-2 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Home className="w-4 h-4 text-accent" />
            <span className="font-archivo text-xs font-bold uppercase tracking-wider">
              Home Assistant Connected
            </span>
          </div>
          <NavLink to="/effects" className="font-archivo text-xs font-bold uppercase tracking-wider hover:text-accent flex items-center gap-1">
            Effect Tester
          </NavLink>
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t-2 border-navy bg-navy text-cream py-4">
        <div className="max-w-[1920px] mx-auto px-6 flex justify-between items-center">
          <span className="font-archivo text-xs uppercase tracking-wider opacity-60">
            GameSync &copy; {new Date().getFullYear()} &mdash; Self-hosted &amp; Free
          </span>
          <a
            href="https://github.com/jwlmson/gamesync"
            target="_blank"
            rel="noopener"
            className="font-archivo text-xs uppercase tracking-wider hover:text-accent"
          >
            GitHub
          </a>
        </div>
      </footer>
    </div>
  );
}
