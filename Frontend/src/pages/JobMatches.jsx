import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Briefcase, MapPin, Clock, ExternalLink, Filter, TrendingUp, Target } from 'lucide-react';
import { getJobs } from '../lib/api';

const _fallback = [
  { title:'Software Engineer — Backend', company:'Infosys', location:'Pune', type:'Full-time', posted:'2 days ago', match:88, tier:'apply', skills:['Java','Spring Boot','SQL'], salary:'₹6–9 LPA', fixes:0 },
  { title:'Junior Data Analyst', company:'TCS Digital', location:'Hyderabad', type:'Full-time', posted:'1 day ago', match:82, tier:'apply', skills:['Python','SQL','Excel'], salary:'₹5–7 LPA', fixes:0 },
  { title:'SDE-1 (React + Node)', company:'Freshworks', location:'Chennai / Remote', type:'Full-time', posted:'3 days ago', match:75, tier:'apply', skills:['React','Node.js','REST API'], salary:'₹8–12 LPA', fixes:1 },
  { title:'Product Analyst', company:'Razorpay', location:'Bangalore', type:'Full-time', posted:'5 days ago', match:68, tier:'reach', skills:['SQL','Product Sense','Analytics'], salary:'₹10–14 LPA', fixes:2 },
  { title:'ML Engineer — Intern to FTE', company:'Observe.AI', location:'Remote', type:'Hybrid', posted:'1 week ago', match:62, tier:'reach', skills:['Python','ML','NLP'], salary:'₹8–11 LPA', fixes:3 },
  { title:'Software Engineer — Google', company:'Google India', location:'Hyderabad', type:'Full-time', posted:'4 days ago', match:38, tier:'dream', skills:['DSA','System Design','Go'], salary:'₹25–40 LPA', fixes:5 },
];

const tierConfig = {
  apply: { label:'Apply Now', color:'#10B981', bg:'rgba(16,185,129,0.1)', border:'rgba(16,185,129,0.25)', desc:'Strong match — your profile fits this role now.' },
  reach: { label:'Reach Role', color:'#F59E0B', bg:'rgba(245,158,11,0.1)', border:'rgba(245,158,11,0.25)', desc:'2–3 fixes needed before applying.' },
  dream: { label:'Dream Role', color:'#6366F1', bg:'rgba(99,102,241,0.1)', border:'rgba(99,102,241,0.25)', desc:'Focus here after you hit HireScore 78+.' },
};

const _tierFor = (m) => m >= 70 ? 'apply' : m >= 40 ? 'reach' : 'dream';

const JobMatches = () => {
  const [filter, setFilter] = useState('all');
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    getJobs().then((data) => {
      setJobs((data || []).map((j) => ({
        title: j.title,
        company: j.company,
        location: j.location,
        type: 'Full-time',
        posted: 'Recently',
        match: Math.round(j.match_score || 0),
        tier: _tierFor(j.match_score || 0),
        skills: j.skills || [],
        salary: '—',
        fixes: Math.max(0, Math.round((100 - (j.match_score || 0)) / 20)),
      })));
    }).catch(() => setJobs(_fallback));
  }, []);

  const filtered = filter === 'all' ? jobs : jobs.filter(j => j.tier === filter);

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="font-display font-bold text-2xl text-white flex items-center gap-2 mb-1"><Briefcase className="w-5 h-5 text-primary" />Job Matches</h1>
          <p className="text-textMuted text-sm">Calibrated to your HireScore of 61 — sorted by your actual match probability</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {[['all','All'],['apply','Apply Now'],['reach','Reach'],['dream','Dream']].map(([v,l])=>(
            <button key={v} onClick={()=>setFilter(v)} className={`text-xs px-3 py-1.5 rounded-full font-medium transition-all ${filter===v?'bg-primary text-white':'text-textMuted border border-white/10 hover:border-primary/30 hover:text-white'}`}>{l}</button>
          ))}
        </div>
      </div>

      {/* Tier legend */}
      <div className="grid grid-cols-3 gap-3">
        {Object.entries(tierConfig).map(([key,cfg])=>(
          <div key={key} className="rounded-xl p-3 text-center" style={{background:cfg.bg,border:`1px solid ${cfg.border}`}}>
            <p className="text-xs font-bold mb-0.5" style={{color:cfg.color}}>{cfg.label}</p>
            <p className="text-textMuted text-xs hidden sm:block">{cfg.desc}</p>
          </div>
        ))}
      </div>

      <div className="space-y-4">
        {filtered.map((job, i) => {
          const cfg = tierConfig[job.tier];
          return (
            <motion.div key={i} initial={{opacity:0,y:15}} animate={{opacity:1,y:0}} transition={{delay:i*0.07}} className="card-hover p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex gap-4 items-start flex-1 min-w-0">
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center font-display font-bold text-lg flex-shrink-0 text-white" style={{background:'rgba(99,102,241,0.15)',border:'1px solid rgba(99,102,241,0.2)'}}>
                    {job.company.charAt(0)}
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-white font-semibold truncate">{job.title}</h3>
                    <p className="text-textMuted text-sm">{job.company}</p>
                    <div className="flex flex-wrap gap-3 mt-1.5 text-xs text-textMuted">
                      <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{job.location}</span>
                      <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{job.posted}</span>
                      <span className="font-medium text-white/70">{job.salary}</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {job.skills.map((s,si)=><span key={si} className="tag text-xs">{s}</span>)}
                    </div>
                  </div>
                </div>

                <div className="flex flex-col items-end gap-2 flex-shrink-0">
                  <div className="text-right">
                    <p className="font-display font-bold text-2xl text-white">{job.match}<span className="text-sm text-textMuted">%</span></p>
                    <p className="text-textMuted text-xs">match</p>
                  </div>
                  <span className="text-xs font-bold px-2.5 py-1 rounded-full" style={{background:cfg.bg,color:cfg.color,border:`1px solid ${cfg.border}`}}>{cfg.label}</span>
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between gap-4">
                <div className="flex-1">
                  <div className="progress-bar"><div className="progress-fill" style={{width:`${job.match}%`,background:job.match>=75?'linear-gradient(90deg,#10B981,#22D3EE)':job.match>=60?'linear-gradient(90deg,#F59E0B,#F97316)':'linear-gradient(90deg,#6366F1,#8B5CF6)'}} /></div>
                </div>
                {job.fixes > 0 && (
                  <span className="text-xs text-textMuted flex-shrink-0"><Target className="w-3 h-3 inline mr-1" />{job.fixes} fix{job.fixes>1?'es':''} needed</span>
                )}
                <a href="#" className="btn-primary text-xs px-4 py-2 flex items-center gap-1.5">
                  Apply <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="card text-center py-8" style={{border:'1px dashed rgba(99,102,241,0.2)'}}>
        <TrendingUp className="w-8 h-8 text-primary mx-auto mb-3" />
        <p className="text-white font-semibold mb-1">Improve your HireScore to unlock more roles</p>
        <p className="text-textMuted text-sm">At 78+ you qualify for 3× more dream roles. Complete your roadmap to get there.</p>
      </div>
    </div>
  );
};
export default JobMatches;
