import { NavLink } from 'react-router-dom';
import { LayoutDashboard, BarChart3, Map, MessageSquare, Trophy, Briefcase, User } from 'lucide-react';

const links = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/results', icon: BarChart3, label: 'Analysis' },
  { to: '/roadmap', icon: Map, label: 'Roadmap' },
  { to: '/coach', icon: MessageSquare, label: 'AI Coach' },
  { to: '/progress', icon: Trophy, label: 'Progress' },
  { to: '/jobs', icon: Briefcase, label: 'Job Matches' },
  { to: '/profile', icon: User, label: 'Profile' },
];

const Sidebar = () => (
  <aside className="w-56 flex-shrink-0 hidden md:flex flex-col py-6 px-3 border-r border-white/5" style={{background:'rgba(8,13,26,0.6)', backdropFilter:'blur(20px)'}}>
    <nav className="space-y-1">
      {links.map(({ to, icon: Icon, label }) => (
        <NavLink key={to} to={to} className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
          <Icon className="w-4 h-4 flex-shrink-0" />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
    <div className="mt-auto">
      <div className="rounded-xl p-4" style={{background:'rgba(99,102,241,0.08)', border:'1px solid rgba(99,102,241,0.15)'}}>
        <p className="text-xs font-semibold text-primary mb-1">HireScore™</p>
        <p className="text-2xl font-display font-bold text-white">61<span className="text-sm text-textMuted">/100</span></p>
        <div className="progress-bar mt-2"><div className="progress-fill" style={{width:'61%'}} /></div>
        <p className="text-xs text-textMuted mt-1.5">+8 pts this week</p>
      </div>
    </div>
  </aside>
);
export default Sidebar;
