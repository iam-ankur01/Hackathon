import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Circle, ChevronRight, Map, Calendar, Target } from 'lucide-react';
import { getRoadmap } from '../lib/api';

const _defaultPhases = [
  { phase:'Week 1–2', label:'Quick Wins', color:'#22D3EE', tasks:[
    { text:'Fix LinkedIn headline — remove "aspiring developer"', done:true },
    { text:'Add README to top 3 GitHub repos', done:true },
    { text:'Add quantifiable results to 3 resume bullet points', done:false },
    { text:'Practice 5 STAR behavioral answers', done:false },
  ]},
  { phase:'Week 3–6', label:'Skill Building', color:'#6366F1', tasks:[
    { text:'Study system design: CAP theorem, SQL vs NoSQL, caching', done:false },
    { text:'Complete 20 LeetCode medium problems (focus: arrays, trees)', done:false },
    { text:'Record and review 3 mock interviews using HireSight', done:false },
    { text:'Build one full-stack project relevant to target role', done:false },
    { text:'Reduce filler words to under 1.5/min (daily practice)', done:false },
  ]},
  { phase:'Week 7–12', label:'Application Push', color:'#8B5CF6', tasks:[
    { text:'Apply to 5 target roles per week', done:false },
    { text:'Personalize resume for each JD — use ATS keywords', done:false },
    { text:'Request LinkedIn recommendations from 2 people', done:false },
    { text:'Re-analyze each failed interview with PostMortem mode', done:false },
    { text:'Reach HireScore of 78+ before bulk applying', done:false },
  ]},
];

const Roadmap = () => {
  const [phases, setPhases] = useState(_defaultPhases);
  const [focus, setFocus] = useState('');
  const [tasks, setTasks] = useState(_defaultPhases.map(p=>p.tasks));

  useEffect(() => {
    getRoadmap().then((r) => {
      setFocus(r.focus_area || '');
      // Wrap backend weekly plan as phase 1, keep the rest of default phases
      if (r.plan && r.plan.length) {
        const aiPhase = {
          phase: `Personalized (${r.focus_area || 'focus'})`,
          label: 'AI-Recommended Focus',
          color: '#22D3EE',
          tasks: r.plan.map(p => ({ text: `Week ${p.week}: ${p.goal}`, done: false })),
        };
        const merged = [aiPhase, ..._defaultPhases];
        setPhases(merged);
        setTasks(merged.map(p => p.tasks));
      }
    }).catch(() => {});
  }, []);


  const toggle = (pi, ti) => {
    const updated = tasks.map((t,i)=>i===pi?t.map((task,j)=>j===ti?{...task,done:!task.done}:task):t);
    setTasks(updated);
  };
  const total = tasks.flat().length;
  const done = tasks.flat().filter(t=>t.done).length;

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display font-bold text-2xl text-white mb-1 flex items-center gap-2"><Map className="w-5 h-5 text-primary" />Your 90-Day Roadmap</h1>
          <p className="text-textMuted text-sm">Personalized based on your interview analysis and HireScore gaps</p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-display font-bold text-white">{done}<span className="text-textMuted text-lg">/{total}</span></p>
          <p className="text-xs text-textMuted">tasks complete</p>
        </div>
      </div>

      <div className="card">
        <div className="flex justify-between text-xs text-textMuted mb-2">
          <span>Overall Progress</span><span>{Math.round(done/total*100)}%</span>
        </div>
        <div className="progress-bar h-2"><div className="progress-fill" style={{width:`${done/total*100}%`}} /></div>
      </div>

      <div className="space-y-5">
        {phases.map((ph, pi) => {
          const pDone = tasks[pi].filter(t=>t.done).length;
          return (
            <motion.div key={pi} initial={{opacity:0,y:15}} animate={{opacity:1,y:0}} transition={{delay:pi*0.1}} className="card">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center font-display font-bold text-white text-sm" style={{background:`${ph.color}20`,border:`1px solid ${ph.color}40`,color:ph.color}}>{pi+1}</div>
                  <div>
                    <p className="text-white font-semibold">{ph.label}</p>
                    <p className="text-textMuted text-xs flex items-center gap-1"><Calendar className="w-3 h-3" />{ph.phase}</p>
                  </div>
                </div>
                <span className="text-xs font-semibold" style={{color:ph.color}}>{pDone}/{tasks[pi].length} done</span>
              </div>
              <div className="space-y-2">
                {tasks[pi].map((task, ti) => (
                  <button key={ti} onClick={()=>toggle(pi,ti)} className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-white/3 transition-all text-left group">
                    {task.done
                      ? <CheckCircle2 className="w-5 h-5 flex-shrink-0" style={{color:ph.color}} />
                      : <Circle className="w-5 h-5 text-textMuted flex-shrink-0 group-hover:text-white transition-colors" />}
                    <span className={`text-sm ${task.done?'text-textMuted line-through':'text-textMain'}`}>{task.text}</span>
                  </button>
                ))}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
export default Roadmap;
