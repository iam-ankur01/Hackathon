import { Link, useNavigate } from 'react-router-dom';
import { Bell, LogOut, User } from 'lucide-react';

const Navbar = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const handleLogout = () => { onLogout(); navigate('/'); };
  return (
    <header className="h-16 flex-shrink-0 flex items-center px-6 border-b border-white/5" style={{background:'rgba(8,13,26,0.95)', backdropFilter:'blur(20px)', position:'sticky', top:0, zIndex:50}}>
      <Link to="/dashboard" className="flex items-center gap-2 font-display font-bold text-xl">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold" style={{background:'linear-gradient(135deg,#6366F1,#22D3EE)'}}>H</div>
        <span className="text-white">Hire<span className="text-primary">Sight</span></span>
      </Link>
      <div className="ml-auto flex items-center gap-3">
        {user && (
          <>
            <button className="w-9 h-9 rounded-xl flex items-center justify-center text-textMuted hover:text-white hover:bg-white/5 transition-all">
              <Bell className="w-4 h-4" />
            </button>
            <Link to="/profile" className="flex items-center gap-2 px-3 py-1.5 rounded-xl hover:bg-white/5 transition-all">
              <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white" style={{background:'linear-gradient(135deg,#6366F1,#8B5CF6)'}}>
                {user.name?.charAt(0)?.toUpperCase() || 'U'}
              </div>
              <span className="text-sm text-textMuted hidden sm:block">{user.name}</span>
            </Link>
            <button onClick={handleLogout} className="w-9 h-9 rounded-xl flex items-center justify-center text-textMuted hover:text-error hover:bg-error/10 transition-all">
              <LogOut className="w-4 h-4" />
            </button>
          </>
        )}
      </div>
    </header>
  );
};
export default Navbar;
