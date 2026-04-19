import { Link, useNavigate } from 'react-router-dom';
import { Bell, LogOut } from 'lucide-react';

const Navbar = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const handleLogout = () => { onLogout(); navigate('/'); };
  return (
    <header className="h-16 flex-shrink-0 flex items-center px-6" style={{background:'rgba(255,255,255,0.9)', backdropFilter:'blur(16px)', borderBottom:'1px solid rgba(10,10,10,0.07)', position:'sticky', top:0, zIndex:50}}>
      <Link to="/dashboard" className="flex items-center gap-2 font-display text-xl" style={{letterSpacing:'-0.04em', fontWeight:700}}>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold" style={{background:'#6d28d9'}}>H</div>
        <span style={{color:'#0a0a0a'}}>Hire<span style={{color:'#6d28d9'}}>Sight</span></span>
      </Link>
      <div className="ml-auto flex items-center gap-3">
        {user && (
          <>
            <button className="w-9 h-9 rounded-xl flex items-center justify-center transition-all" style={{color:'#71717a'}} onMouseEnter={e=>{e.currentTarget.style.background='#f4f4f5';e.currentTarget.style.color='#0a0a0a'}} onMouseLeave={e=>{e.currentTarget.style.background='transparent';e.currentTarget.style.color='#71717a'}}>
              <Bell className="w-4 h-4" />
            </button>
            <Link to="/profile" className="flex items-center gap-2 px-3 py-1.5 rounded-xl transition-all" onMouseEnter={e=>e.currentTarget.style.background='#f4f4f5'} onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
              <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white" style={{background:'#6d28d9'}}>
                {user.name?.charAt(0)?.toUpperCase() || 'U'}
              </div>
              <span className="text-sm hidden sm:block" style={{color:'#0a0a0a', fontWeight:500}}>{user.name}</span>
            </Link>
            <button onClick={handleLogout} className="w-9 h-9 rounded-xl flex items-center justify-center transition-all" style={{color:'#71717a'}} onMouseEnter={e=>{e.currentTarget.style.background='#fef2f2';e.currentTarget.style.color='#b91c1c'}} onMouseLeave={e=>{e.currentTarget.style.background='transparent';e.currentTarget.style.color='#71717a'}}>
              <LogOut className="w-4 h-4" />
            </button>
          </>
        )}
      </div>
    </header>
  );
};
export default Navbar;
