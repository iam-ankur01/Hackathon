import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Eye, EyeOff, ArrowRight, User, Mail, Lock, Briefcase, GraduationCap } from 'lucide-react';
import { login as apiLogin, signup as apiSignup, saveSession, updateProfile } from '../lib/api';

const Login = ({ onLogin }) => {
  const [isSignup, setIsSignup] = useState(false);
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ name:'', email:'', password:'', role:'Software Engineer', level:'Fresher', college:'' });
  const navigate = useNavigate();

  const roles = ['Software Engineer','Data Scientist','Product Manager','Business Analyst','DevOps Engineer','UI/UX Designer','Consulting','Marketing','Sales','HR'];
  const levels = ['Fresher (0–1 yr)','Junior (1–3 yrs)','Mid-level (3–6 yrs)','Senior (6+ yrs)'];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      let session;
      if (isSignup) {
        session = await apiSignup({
          name: form.name, email: form.email, password: form.password,
          role: form.role, college: form.college,
        });
        saveSession(session);
        // persist level too
        if (form.level) {
          const updated = await updateProfile({ level: form.level });
          session = { ...session, user: updated };
          saveSession(session);
        }
      } else {
        session = await apiLogin({ email: form.email, password: form.password });
        saveSession(session);
      }
      onLogin(session.user);
      navigate('/dashboard');
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left panel */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-12 relative overflow-hidden" style={{background:'#0a0a0a'}}>
        <Link to="/" className="relative flex items-center gap-2 font-display text-xl" style={{fontWeight:700, letterSpacing:'-0.04em'}}>
          <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold" style={{background:'#6d28d9'}}>H</div>
          <span style={{color:'#ffffff'}}>Hire<span style={{color:'#a78bfa'}}>Sight</span></span>
        </Link>
        <div className="relative">
          <h2 className="font-display mb-8" style={{fontSize:'clamp(2rem,4vw,3.5rem)', fontWeight:700, letterSpacing:'-0.04em', lineHeight:1.05, color:'#ffffff'}}>
            Know exactly where<br/>you lost the <span className="gold-underline" style={{color:'#a78bfa'}}>opportunity.</span>
          </h2>
          <div className="space-y-4">
            {['Second-by-second confidence analysis','GitHub & LinkedIn profile audit','AI-generated improvement roadmap','Personal AI coach that knows your history'].map((t,i)=>(
              <div key={i} className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0" style={{background:'rgba(245,197,24,0.15)'}}>
                  <div className="w-1.5 h-1.5 rounded-full" style={{background:'#f5c518'}} />
                </div>
                <span className="text-sm" style={{color:'#a1a1aa'}}>{t}</span>
              </div>
            ))}
          </div>
        </div>
        <p className="relative text-xs" style={{color:'#71717a'}}>© 2026 HireSight</p>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex items-center justify-center p-6">
        <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} className="w-full max-w-md">
          <div className="mb-8">
            <Link to="/" className="lg:hidden flex items-center gap-2 font-display text-xl mb-8" style={{fontWeight:700, letterSpacing:'-0.04em'}}>
              <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold" style={{background:'#6d28d9'}}>H</div>
              <span style={{color:'#0a0a0a'}}>Hire<span style={{color:'#6d28d9'}}>Sight</span></span>
            </Link>
            <h1 className="font-display font-bold text-3xl text-white mb-2">
              {isSignup ? 'Create your account' : 'Welcome back'}
            </h1>
            <p className="text-textMuted">{isSignup ? 'Start your journey to interview mastery' : 'Sign in to your HireSight dashboard'}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignup && (
              <div>
                <label className="block text-xs font-semibold text-textMuted mb-1.5 uppercase tracking-wide">Full Name</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textMuted" />
                  <input className="input-field pl-10" placeholder="Onkar Kulkarni" value={form.name} onChange={e=>setForm({...form,name:e.target.value})} required />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-textMuted mb-1.5 uppercase tracking-wide">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textMuted" />
                <input type="email" className="input-field pl-10" placeholder="you@example.com" value={form.email} onChange={e=>setForm({...form,email:e.target.value})} required />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-textMuted mb-1.5 uppercase tracking-wide">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textMuted" />
                <input type={showPass?'text':'password'} className="input-field pl-10 pr-10" placeholder="••••••••" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} required />
                <button type="button" onClick={()=>setShowPass(!showPass)} className="absolute right-3 top-1/2 -translate-y-1/2 text-textMuted hover:text-white transition-colors">
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {isSignup && (
              <>
                <div>
                  <label className="block text-xs font-semibold text-textMuted mb-1.5 uppercase tracking-wide">Target Role</label>
                  <div className="relative">
                    <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textMuted" />
                    <select className="input-field pl-10 appearance-none" value={form.role} onChange={e=>setForm({...form,role:e.target.value})}>
                      {roles.map(r=><option key={r}>{r}</option>)}
                    </select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-textMuted mb-1.5 uppercase tracking-wide">Experience</label>
                    <select className="input-field text-sm appearance-none" value={form.level} onChange={e=>setForm({...form,level:e.target.value})}>
                      {levels.map(l=><option key={l}>{l}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-textMuted mb-1.5 uppercase tracking-wide">College / Company</label>
                    <div className="relative">
                      <GraduationCap className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textMuted" />
                      <input className="input-field pl-10 text-sm" placeholder="SPPU / TCS" value={form.college} onChange={e=>setForm({...form,college:e.target.value})} />
                    </div>
                  </div>
                </div>
              </>
            )}

            {error && <p className="text-error text-sm">{error}</p>}

            <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2 mt-6 py-3.5">
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>{isSignup ? 'Create Account' : 'Sign In'} <ArrowRight className="w-4 h-4" /></>
              )}
            </button>
          </form>

          <p className="text-center text-textMuted text-sm mt-6">
            {isSignup ? 'Already have an account?' : "Don't have an account?"}{' '}
            <button onClick={()=>setIsSignup(!isSignup)} className="text-primary-light font-semibold hover:underline">
              {isSignup ? 'Sign in' : 'Sign up free'}
            </button>
          </p>
        </motion.div>
      </div>
    </div>
  );
};
export default Login;
