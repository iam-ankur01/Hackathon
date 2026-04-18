import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Trophy, Zap, Flame, Star, Lock, TrendingUp, BarChart3 } from 'lucide-react';
import { getProgress, getDashboard } from '../lib/api';

const badges = [
  { icon:'🔬', title:'First Autopsy', desc:'Uploaded your first interview', xp:100, earned:true },
  { icon:'✍️', title:'Profile Glow-Up', desc:'Updated LinkedIn headline', xp:50, earned:true },
  { icon:'🗓️', title:'Week 1 Warrior', desc:'Completed week 1 of roadmap', xp:200, earned:false },
  { icon:'📈', title:'Level Up', desc:'HireScore improved by 10+ pts', xp:300, earned:false },
  { icon:'🎯', title:'On The Hunt', desc:'Applied to 5 jobs', xp:150, earned:false },
  { icon:'🔥', title:'Consistent', desc:'7-day platform streak', xp:250, earned:false },
  { icon:'💬', title:'Filler Fighter', desc:'Filler words under 1.5/min', xp:200, earned:false },
  { icon:'⭐', title:'STAR Master', desc:'90%+ STAR score on any answer', xp:350, earned:false },
];

const weeklyData = [
  { day:'Mon', score:58 }, { day:'Tue', score:59 }, { day:'Wed', score:60 },
  { day:'Thu', score:61 }, { day:'Fri', score:63 }, { day:'Sat', score:61 }, { day:'Sun', score:61 },
];

const activityLog = [
  { action:'Uploaded interview recording', xp:'+100 XP', time:'2h ago', icon:'📤' },
  { action:'Completed 3 roadmap tasks', xp:'+75 XP', time:'Yesterday', icon:'✅' },
  { action:'Chatted with Max for 15 min', xp:'+25 XP', time:'Yesterday', icon:'💬' },
  { action:'Reviewed Results page', xp:'+10 XP', time:'2 days ago', icon:'📊' },
  { action:'Updated LinkedIn headline', xp:'+50 XP', time:'3 days ago', icon:'✍️' },
];

const levels = ['Rookie','Contender','Strong Candidate','Job-Ready','Hired'];

const Progress = ({ user }) => {
  const [series, setSeries] = useState([]);
  const [hirescore, setHirescore] = useState(0);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    Promise.all([getProgress(), getDashboard()]).then(([p, d]) => {
      setSeries((p.series || []).slice(-7).map(s => ({
        day: (s.date || '').slice(5, 10),
        score: Math.round(s.score || 0),
      })));
      setHirescore(d.hirescore || 0);
      setTotal(p.total || 0);
    }).catch(() => {});
  }, []);

  const xp = total * 100;
  const nextLevel = Math.max(1000, Math.ceil((xp + 1) / 1000) * 1000);
  const currentLevel = Math.min(4, Math.floor(xp / 1000));
  const streak = total;

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <h1 className="font-display font-bold text-2xl text-white flex items-center gap-2"><Trophy className="w-5 h-5 text-warning" />Progress Tracker</h1>

      {/* Top stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label:'Total XP', val:xp.toLocaleString(), icon:Zap, color:'#6366F1' },
          { label:'Current Level', val:levels[currentLevel], icon:Star, color:'#F59E0B' },
          { label:'Day Streak', val:`${streak} days`, icon:Flame, color:'#EF4444' },
          { label:'HireScore', val:`${hirescore} / 100`, icon:TrendingUp, color:'#10B981' },
        ].map((s,i)=>(
          <motion.div key={i} initial={{opacity:0,y:15}} animate={{opacity:1,y:0}} transition={{delay:i*0.08}} className="card flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{background:`${s.color}18`,border:`1px solid ${s.color}30`}}>
              <s.icon className="w-5 h-5" style={{color:s.color}} />
            </div>
            <div>
              <p className="font-display font-bold text-white text-lg leading-tight">{s.val}</p>
              <p className="text-textMuted text-xs">{s.label}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* XP progress to next level */}
      <motion.div initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} className="card">
        <div className="flex justify-between items-center mb-3">
          <div>
            <p className="text-white font-semibold">Level {currentLevel+1}: <span className="text-primary-light">{levels[currentLevel]}</span></p>
            <p className="text-textMuted text-xs">{nextLevel - xp} XP to next level — <span className="text-warning font-medium">{levels[currentLevel+1]}</span></p>
          </div>
          <span className="font-display font-bold text-white text-xl">{xp} <span className="text-textMuted text-sm font-normal">/ {nextLevel} XP</span></span>
        </div>
        <div className="progress-bar h-3"><div className="progress-fill" style={{width:`${xp/nextLevel*100}%`}} /></div>
        <div className="flex justify-between mt-3">
          {levels.map((l,i)=>(
            <div key={i} className="flex flex-col items-center gap-1">
              <div className={`w-3 h-3 rounded-full ${i<=currentLevel?'bg-primary':'bg-white/10'}`} />
              <span className={`text-xs hidden sm:block ${i<=currentLevel?'text-primary-light':'text-textMuted'}`}>{l.split(' ')[0]}</span>
            </div>
          ))}
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* HireScore chart */}
        <motion.div initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} transition={{delay:0.1}} className="card">
          <h3 className="font-semibold text-white mb-4 flex items-center gap-2"><BarChart3 className="w-4 h-4 text-primary" />Score Over Time</h3>
          <div className="flex items-end gap-2 h-36">
            {(series.length ? series : weeklyData).map((d,i,arr)=>{
              const height = Math.max(8, (d.score / 100) * 100);
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                  <span className="text-xs text-textMuted">{d.score}</span>
                  <div className="w-full rounded-t-lg transition-all" style={{height:`${height}%`,background:i===arr.length-1?'linear-gradient(180deg,#22D3EE,#6366F1)':'rgba(99,102,241,0.35)',minHeight:8}} />
                  <span className="text-xs text-textMuted">{d.day}</span>
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* Activity log */}
        <motion.div initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} transition={{delay:0.15}} className="card">
          <h3 className="font-semibold text-white mb-4 flex items-center gap-2"><Zap className="w-4 h-4 text-accent" />Recent Activity</h3>
          <div className="space-y-3">
            {activityLog.map((a,i)=>(
              <div key={i} className="flex items-center gap-3">
                <span className="text-lg flex-shrink-0">{a.icon}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm truncate">{a.action}</p>
                  <p className="text-textMuted text-xs">{a.time}</p>
                </div>
                <span className="text-xs font-semibold text-success flex-shrink-0">{a.xp}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Badges */}
      <motion.div initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} transition={{delay:0.2}} className="card">
        <h3 className="font-semibold text-white mb-5 flex items-center gap-2"><Trophy className="w-4 h-4 text-warning" />Badges</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {badges.map((b,i)=>(
            <div key={i} className={`flex flex-col items-center text-center p-4 rounded-xl transition-all ${b.earned?'':'opacity-40'}`} style={{background:b.earned?'rgba(99,102,241,0.08)':'rgba(255,255,255,0.03)',border:`1px solid ${b.earned?'rgba(99,102,241,0.25)':'rgba(255,255,255,0.05)'}`}}>
              <span className="text-3xl mb-2">{b.earned ? b.icon : '🔒'}</span>
              <p className="text-white text-xs font-semibold mb-0.5">{b.title}</p>
              <p className="text-textMuted text-xs leading-tight mb-2">{b.desc}</p>
              <span className={`text-xs font-bold ${b.earned?'text-warning':'text-textMuted'}`}>+{b.xp} XP</span>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};
export default Progress;
