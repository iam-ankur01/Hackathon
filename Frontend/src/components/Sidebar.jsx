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
  <aside className="w-56 flex-shrink-0 hidden md:flex flex-col py-6 px-3" style={{background:'#fafafa', borderRight:'1px solid rgba(10,10,10,0.07)'}}>
    <nav className="space-y-1">
      {links.map(({ to, icon: Icon, label }) => (
        <NavLink key={to} to={to} className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
          <Icon className="w-4 h-4 flex-shrink-0" />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
    <div className="mt-auto">
      <div className="rounded-xl p-4" style={{background:'#0a0a0a', color:'#fafafa'}}>
        <p className="text-xs font-semibold mb-1" style={{color:'#f5c518', letterSpacing:'0.08em', textTransform:'uppercase'}}>HireScore</p>
        <p className="text-3xl font-display tracking-tightest" style={{fontWeight:700, color:'#ffffff'}}>61<span className="text-sm font-normal" style={{color:'#a1a1aa'}}>/100</span></p>
        <div className="mt-2" style={{height:6, borderRadius:3, background:'rgba(255,255,255,0.1)', overflow:'hidden'}}>
          <div style={{height:'100%', width:'61%', background:'#6d28d9', borderRadius:3}} />
        </div>
        <p className="text-xs mt-1.5" style={{color:'#a1a1aa'}}>+8 pts this week</p>
      </div>
    </div>
  </aside>
);
export default Sidebar;
