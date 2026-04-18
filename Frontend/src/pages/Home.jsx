import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Brain, BarChart3, Map, MessageSquare, Trophy, Upload, Mic, Github, Linkedin } from 'lucide-react';

const features = [
  { icon: Upload, title: 'Upload Any Interview', desc: 'Drop your audio, video, or paste a Zoom recording link. We handle the rest.' },
  { icon: Brain, title: 'AI Deep Analysis', desc: 'Speech patterns, confidence drops, filler words, STAR structure — all analyzed second by second.' },
  { icon: BarChart3, title: 'Profile Intelligence', desc: 'We audit your GitHub, LinkedIn, and resume against the job description to find hidden gaps.' },
  { icon: Map, title: 'Personalized Roadmap', desc: 'A 30/60/90 day improvement plan built specifically from your weaknesses, not generic advice.' },
  { icon: MessageSquare, title: 'AI Coach Max', desc: 'Chat with your personal AI career coach who knows your full profile and history.' },
  { icon: Trophy, title: 'Gamified Progress', desc: 'Earn XP, unlock badges, and level up your HireScore as you improve.' },
];

const stats = [
  { val: '3.4×', label: 'Higher offer rate for users' },
  { val: '89%', label: 'Report more confidence' },
  { val: '12min', label: 'Average debrief time' },
  { val: '50K+', label: 'Interviews analyzed' },
];

const Home = ({ onLogin }) => {
  const navigate = useNavigate();
  const handleDemo = () => {
    onLogin({ name: 'Demo User', email: 'demo@hiresight.ai', role: 'Software Engineer' });
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-background text-textMain overflow-x-hidden">
      {/* Nav */}
      <header className="fixed top-0 w-full z-50 flex items-center px-6 h-16 border-b border-white/5" style={{background:'rgba(8,13,26,0.95)',backdropFilter:'blur(20px)'}}>
        <div className="flex items-center gap-2 font-display font-bold text-xl">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold" style={{background:'linear-gradient(135deg,#6366F1,#22D3EE)'}}>H</div>
          <span className="text-white">Hire<span className="text-primary-light">Sight</span></span>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <Link to="/login" className="btn-ghost text-sm px-4 py-2">Sign in</Link>
          <Link to="/login" className="btn-primary text-sm px-4 py-2">Get started</Link>
        </div>
      </header>

      {/* Hero */}
      <section className="relative min-h-screen flex flex-col items-center justify-center text-center px-4 pt-16 overflow-hidden">
        <div className="absolute inset-0 bg-grid-pattern" style={{backgroundSize:'40px 40px'}} />
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full pointer-events-none" style={{background:'radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%)'}} />
        <div className="absolute top-1/2 left-1/4 w-[300px] h-[300px] rounded-full pointer-events-none" style={{background:'radial-gradient(circle, rgba(34,211,238,0.06) 0%, transparent 70%)'}} />

        <motion.div initial={{opacity:0,y:30}} animate={{opacity:1,y:0}} transition={{duration:0.8}} className="relative z-10 max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold mb-8" style={{background:'rgba(99,102,241,0.12)',border:'1px solid rgba(99,102,241,0.25)',color:'#818CF8'}}>
            <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
            DevClash 2026 — Hackathon Project
          </div>

          <h1 className="font-display font-bold text-5xl md:text-7xl leading-tight text-white mb-6">
            Know exactly why you<br />
            <span style={{background:'linear-gradient(135deg,#6366F1,#22D3EE)',WebkitBackgroundClip:'text',WebkitTextFillColor:'transparent'}}>didn't get the job</span>
          </h1>

          <p className="text-lg md:text-xl text-textMuted max-w-2xl mx-auto mb-10 leading-relaxed">
            Upload your interview recording and get a second-by-second breakdown of where you lost the recruiter — with a full roadmap to fix it before the next one.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/login" className="btn-primary text-base px-8 py-4 flex items-center justify-center gap-2">
              Analyze my interview <ArrowRight className="w-4 h-4" />
            </Link>
            <button onClick={handleDemo} className="btn-ghost text-base px-8 py-4">
              View live demo
            </button>
          </div>
        </motion.div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-textMuted text-xs animate-bounce">
          <div className="w-5 h-8 rounded-full border border-white/20 flex items-start justify-center pt-1.5">
            <div className="w-1 h-2 rounded-full bg-primary" />
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-20 px-4 border-y border-white/5" style={{background:'rgba(15,22,40,0.5)'}}>
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((s, i) => (
            <motion.div key={i} initial={{opacity:0,y:20}} whileInView={{opacity:1,y:0}} viewport={{once:true}} transition={{delay:i*0.1}} className="text-center">
              <p className="font-display font-bold text-4xl text-white mb-1">{s.val}</p>
              <p className="text-textMuted text-sm">{s.label}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <p className="tag mb-4">Platform features</p>
            <h2 className="font-display font-bold text-4xl md:text-5xl text-white mb-4">Everything you need to get hired</h2>
            <p className="text-textMuted text-lg max-w-2xl mx-auto">From interview debrief to GitHub audit to AI coaching — one platform for your entire job search.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <motion.div key={i} initial={{opacity:0,y:20}} whileInView={{opacity:1,y:0}} viewport={{once:true}} transition={{delay:i*0.1}} className="card-hover p-6">
                <div className="w-11 h-11 rounded-xl flex items-center justify-center mb-4" style={{background:'rgba(99,102,241,0.12)',border:'1px solid rgba(99,102,241,0.2)'}}>
                  <f.icon className="w-5 h-5 text-primary-light" />
                </div>
                <h3 className="font-display font-semibold text-white text-lg mb-2">{f.title}</h3>
                <p className="text-textMuted text-sm leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Integrations */}
      <section className="py-20 px-4 border-y border-white/5" style={{background:'rgba(15,22,40,0.5)'}}>
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-textMuted text-sm mb-8 uppercase tracking-widest font-semibold">Connects with your existing profiles</p>
          <div className="flex flex-wrap justify-center gap-6">
            {[{icon:Github,label:'GitHub'},{icon:Linkedin,label:'LinkedIn'},{label:'📄',text:'Resume'},{label:'🎥',text:'Zoom'},{label:'✉️',text:'Gmail'}].map((item,i)=>(
              <div key={i} className="flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-medium text-textMuted" style={{background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.08)'}}>
                {item.icon ? <item.icon className="w-4 h-4" /> : <span>{item.label}</span>}
                <span>{item.label || item.text}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-32 px-4 text-center relative overflow-hidden">
        <div className="absolute inset-0" style={{background:'radial-gradient(ellipse at center, rgba(99,102,241,0.15) 0%, transparent 70%)'}} />
        <div className="relative z-10 max-w-2xl mx-auto">
          <h2 className="font-display font-bold text-4xl md:text-5xl text-white mb-6">Ready to stop repeating the same interview mistakes?</h2>
          <p className="text-textMuted text-lg mb-10">Upload your first interview recording — analysis takes under 60 seconds.</p>
          <Link to="/login" className="btn-primary text-lg px-10 py-4 inline-flex items-center gap-2">
            Get started free <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      <footer className="border-t border-white/5 py-8 px-6 text-center text-textMuted text-sm">
        © 2026 HireSight · Built at DevClash 2026 · DevKraft
      </footer>
    </div>
  );
};
export default Home;
