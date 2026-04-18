import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, Sparkles } from 'lucide-react';
import { getCoach } from '../lib/api';

const initialMessages = [
  { role:'ai', text:"Hi! I'm Max, your AI career coach. Loading your latest interview insights…" },
];

const suggestions = ['Practice STAR method with me','How do I reduce filler words?','Review my system design gaps','What jobs should I apply to now?','Fix my LinkedIn headline'];

const autoReply = (msg) => {
  const m = msg.toLowerCase();
  if (m.includes('star')) return "Great choice! Let's practice. Tell me about a project where you solved a difficult problem — and make sure you end with a specific number: impact, time saved, or percentage improvement. Go ahead!";
  if (m.includes('filler') || m.includes('um')) return "Filler words are a confidence signal. The fix is simple: replace every 'um' with a deliberate 1-second pause. It sounds more confident, not less. Try this: record yourself answering 'Tell me about yourself' and count your fillers. How many do you think you have?";
  if (m.includes('system design') || m.includes('technical')) return "Your technical score is 55/100. For system design, focus on three areas this week: (1) CAP theorem — can you explain consistency vs availability in simple terms? (2) Database trade-offs — when SQL vs NoSQL? (3) Caching — why and when? Want me to quiz you on any of these?";
  if (m.includes('linkedin')) return `Your current headline likely says something generic. Here's a stronger formula: [Role] | [Key Skill] | [One achievement or interest]. Example: 'Software Engineer | React & Python | Built ML tools for 10K+ users'. Want me to write yours?`;
  if (m.includes('job') || m.includes('apply')) return "Based on your HireScore of 61, you're a strong fit for roles at mid-size companies and service firms (TCS, Wipro, Capgemini). Your reach targets are product companies. I'd hold on bulk applying until your HireScore hits 72+. Want to see your specific job matches?";
  return "That's a great question. Based on your profile and recent interview, I'd focus on the areas flagged in your debrief first — particularly your STAR answers and technical explanations. What specific part would you like to work on together?";
};

const Coach = ({ user }) => {
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const endRef = useRef();

  useEffect(() => { endRef.current?.scrollIntoView({ behavior:'smooth' }); }, [messages, typing]);

  useEffect(() => {
    getCoach().then((c) => {
      if (c.message) {
        setMessages([{ role:'ai', text: c.message }]);
        return;
      }
      const intro = `Hi! I've reviewed your last interview — you scored ${c.total_score}/100 (grade ${c.grade}). ${c.report_summary || ''}`;
      const tips = (c.coaching?.tips || []).map(t => `• ${t.area}: ${t.tip}`).join('\n');
      const strengths = (c.coaching?.strengths || []).slice(0, 3).join(', ');
      const msgs = [{ role:'ai', text: intro }];
      if (tips) msgs.push({ role:'ai', text: `Your personalized focus areas:\n${tips}` });
      if (strengths) msgs.push({ role:'ai', text: `What you're already doing well: ${strengths}.\n\nWhat would you like to work on first?` });
      setMessages(msgs);
    }).catch(() => {});
  }, []);

  const send = (text) => {
    const msg = text || input.trim();
    if (!msg) return;
    setInput('');
    setMessages(prev=>[...prev,{role:'user',text:msg}]);
    setTyping(true);
    setTimeout(()=>{
      setTyping(false);
      setMessages(prev=>[...prev,{role:'ai',text:autoReply(msg)}]);
    }, 1200);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-64px)]">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/5 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{background:'linear-gradient(135deg,#6366F1,#22D3EE)'}}>
          <Bot className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="font-display font-semibold text-white">Max — Your AI Coach</h2>
          <p className="text-xs text-success flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-success inline-block" />Online · Knows your full profile</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        <AnimatePresence initial={false}>
          {messages.map((m,i)=>(
            <motion.div key={i} initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} className={`flex gap-3 ${m.role==='user'?'flex-row-reverse':''}`}>
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${m.role==='ai'?'bg-primary/20':'bg-white/8'}`}>
                {m.role==='ai' ? <Sparkles className="w-4 h-4 text-primary-light" /> : <User className="w-4 h-4 text-textMuted" />}
              </div>
              <div className={`max-w-lg px-4 py-3 rounded-2xl text-sm leading-relaxed ${m.role==='ai'?'bg-surfaceHigh text-textMain':'text-white'}`} style={m.role==='user'?{background:'linear-gradient(135deg,#6366F1,#8B5CF6)'}:{}}>
                {m.text}
              </div>
            </motion.div>
          ))}
          {typing && (
            <motion.div initial={{opacity:0}} animate={{opacity:1}} className="flex gap-3">
              <div className="w-8 h-8 rounded-xl bg-primary/20 flex items-center justify-center"><Sparkles className="w-4 h-4 text-primary-light" /></div>
              <div className="px-4 py-3 rounded-2xl bg-surfaceHigh flex items-center gap-1">
                {[0,1,2].map(i=><div key={i} className="w-1.5 h-1.5 rounded-full bg-textMuted animate-bounce" style={{animationDelay:`${i*0.15}s`}} />)}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={endRef} />
      </div>

      {/* Suggestions */}
      <div className="px-4 pb-2 flex gap-2 overflow-x-auto scrollbar-none">
        {suggestions.map((s,i)=>(
          <button key={i} onClick={()=>send(s)} className="flex-shrink-0 text-xs px-3 py-1.5 rounded-full border border-white/10 text-textMuted hover:text-white hover:border-primary/40 transition-all">
            {s}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="px-4 pb-4">
        <div className="flex gap-2 p-2 rounded-xl" style={{background:'rgba(15,22,40,0.9)',border:'1px solid rgba(255,255,255,0.08)'}}>
          <input className="flex-1 bg-transparent outline-none text-sm text-textMain placeholder-textMuted px-2" placeholder="Ask Max anything about your interview or career..." value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>e.key==='Enter'&&send()} />
          <button onClick={()=>send()} className="w-9 h-9 rounded-lg flex items-center justify-center text-white flex-shrink-0" style={{background:'linear-gradient(135deg,#6366F1,#8B5CF6)'}}>
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
export default Coach;
