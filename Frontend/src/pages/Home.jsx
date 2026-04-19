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
      <header className="fixed top-0 w-full z-50 flex items-center px-6 h-16" style={{background:'rgba(255,255,255,0.9)', backdropFilter:'blur(16px)', borderBottom:'1px solid rgba(10,10,10,0.07)'}}>
        <div className="flex items-center gap-2 font-display text-xl" style={{fontWeight:700, letterSpacing:'-0.04em'}}>
          <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold" style={{background:'#6d28d9'}}>H</div>
          <span style={{color:'#0a0a0a'}}>Hire<span style={{color:'#6d28d9'}}>Sight</span></span>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <Link to="/login" className="text-sm px-4 py-2 rounded-lg transition-all" style={{color:'#0a0a0a', fontWeight:500}} onMouseEnter={e=>e.currentTarget.style.background='#f4f4f5'} onMouseLeave={e=>e.currentTarget.style.background='transparent'}>Sign in</Link>
          <Link to="/login" className="btn-primary text-sm px-4 py-2">Get started</Link>
        </div>
      </header>

      {/* Hero — Solus-style: big bold display headline, gold "NEW" pill, violet accent with gold underline */}
      <section className="relative min-h-screen flex flex-col justify-center px-8 md:px-16 pt-24 pb-16">
        <motion.div initial={{opacity:0,y:30}} animate={{opacity:1,y:0}} transition={{duration:0.7}} className="relative z-10 max-w-5xl">

          <span className="badge-new mb-8 inline-flex">
            <span style={{background:'#0a0a0a', color:'#fbbf24', padding:'2px 8px', borderRadius:'999px', fontSize:'10px', fontWeight:800, letterSpacing:'0.08em'}}>NEW</span>
            HireSight · AI Interview Debrief
          </span>

          <h1 className="font-display mb-8" style={{fontSize:'clamp(3rem, 8vw, 6.5rem)', fontWeight:700, lineHeight:1.02, letterSpacing:'-0.05em', color:'#0a0a0a'}}>
            Know exactly where<br />
            you lost the <span className="gold-underline" style={{color:'#6d28d9'}}>opportunity.</span>
          </h1>

          <p className="text-lg md:text-xl max-w-2xl mb-10 leading-relaxed" style={{color:'#52525b'}}>
            Upload your interview recording and get a second-by-second breakdown of where you lost the recruiter — with a full roadmap to fix it before the next one.
          </p>

          <div className="flex flex-col sm:flex-row gap-3">
            <Link to="/login" className="btn-primary text-base px-6 py-3.5 flex items-center justify-center gap-2">
              Get Started Free <ArrowRight className="w-4 h-4" />
            </Link>
            <button onClick={handleDemo} className="btn-ghost text-base px-6 py-3.5">
              View live demo
            </button>
          </div>
          <p className="text-sm mt-4" style={{color:'#71717a'}}>No credit card · Free forever</p>
        </motion.div>
      </section>

      {/* Stats */}
      <section className="py-20 px-4" style={{background:'#0a0a0a'}}>
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((s, i) => (
            <motion.div key={i} initial={{opacity:0,y:20}} whileInView={{opacity:1,y:0}} viewport={{once:true}} transition={{delay:i*0.1}} className="text-center">
              <p className="font-display text-5xl mb-1" style={{fontWeight:700, letterSpacing:'-0.04em', color:'#ffffff'}}>{s.val}</p>
              <p className="text-sm" style={{color:'#a1a1aa'}}>{s.label}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <p className="tag mb-4 inline-block">Platform features</p>
            <h2 className="font-display mb-4" style={{fontSize:'clamp(2rem,5vw,3.5rem)', fontWeight:700, letterSpacing:'-0.04em', color:'#0a0a0a'}}>Everything you need to get hired</h2>
            <p className="text-lg max-w-2xl mx-auto" style={{color:'#52525b'}}>From interview debrief to GitHub audit to AI coaching — one platform for your entire job search.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <motion.div key={i} initial={{opacity:0,y:20}} whileInView={{opacity:1,y:0}} viewport={{once:true}} transition={{delay:i*0.1}} className="card-hover p-6">
                <div className="w-11 h-11 rounded-xl flex items-center justify-center mb-4" style={{background:'#faf5ff', border:'1px solid rgba(109,40,217,0.2)'}}>
                  <f.icon className="w-5 h-5" style={{color:'#6d28d9'}} />
                </div>
                <h3 className="font-display text-lg mb-2" style={{fontWeight:700, color:'#0a0a0a', letterSpacing:'-0.02em'}}>{f.title}</h3>
                <p className="text-sm leading-relaxed" style={{color:'#52525b'}}>{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Integrations */}
      <section className="py-20 px-4" style={{background:'#fafafa', borderTop:'1px solid rgba(10,10,10,0.07)', borderBottom:'1px solid rgba(10,10,10,0.07)'}}>
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-sm mb-8 uppercase font-semibold" style={{color:'#71717a', letterSpacing:'0.12em'}}>Connects with your existing profiles</p>
          <div className="flex flex-wrap justify-center gap-3">
            {[{icon:Github,label:'GitHub'},{icon:Linkedin,label:'LinkedIn'},{label:'📄',text:'Resume'},{label:'🎥',text:'Zoom'},{label:'✉️',text:'Gmail'}].map((item,i)=>(
              <div key={i} className="flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-medium" style={{background:'#ffffff', border:'1px solid rgba(10,10,10,0.08)', color:'#0a0a0a'}}>
                {item.icon ? <item.icon className="w-4 h-4" /> : <span>{item.label}</span>}
                <span>{item.label || item.text}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-32 px-4 text-center" style={{background:'#0a0a0a'}}>
        <div className="relative z-10 max-w-2xl mx-auto">
          <h2 className="font-display mb-6" style={{fontSize:'clamp(2rem,5vw,3.5rem)', fontWeight:700, letterSpacing:'-0.04em', color:'#ffffff'}}>Ready to stop repeating the same interview mistakes?</h2>
          <p className="text-lg mb-10" style={{color:'#a1a1aa'}}>Upload your first interview recording — analysis takes under 60 seconds.</p>
          <Link to="/login" className="btn-primary text-lg px-10 py-4 inline-flex items-center gap-2">
            Get started free <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      <footer className="py-8 px-6 text-center text-sm" style={{color:'#71717a', borderTop:'1px solid rgba(10,10,10,0.07)'}}>
        © 2026 HireSight
      </footer>
    </div>
  );
};
export default Home;
