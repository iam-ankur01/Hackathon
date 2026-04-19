import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { BarChart, Bar, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { MessageSquare, Target, ShieldAlert, Lightbulb, Download, Share2 } from 'lucide-react';
import { getInterview, listInterviews } from '../lib/api';

const ScoreRing = ({ score, label, color }) => {
  const circumference = 2 * Math.PI * 36;
  const offset = circumference - (score / 100) * circumference;
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-24 h-24">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 80 80">
          <circle cx="40" cy="40" r="36" fill="none" stroke="rgba(10,10,10,0.08)" strokeWidth="7" />
          <circle cx="40" cy="40" r="36" fill="none" stroke={color} strokeWidth="7" strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round" style={{transition:'stroke-dashoffset 1.5s ease'}} />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="font-display font-bold text-xl" style={{color:'#0a0a0a'}}>{Math.round(score)}</span>
        </div>
      </div>
      <span className="text-textMuted text-xs font-medium text-center">{label}</span>
    </div>
  );
};

const Results = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        let interviewId = id;
        if (!interviewId) {
          // Fall back to the most recent completed interview
          const list = await listInterviews();
          const latest = (list || []).find(x => x.status === 'completed');
          if (!latest) { setError('No interviews yet. Upload one from the Dashboard.'); setLoading(false); return; }
          interviewId = latest.id;
        }
        const full = await getInterview(interviewId);
        setData(full);
      } catch (err) {
        setError(err?.response?.data?.detail || err.message || 'Failed to load report');
      } finally { setLoading(false); }
    })();
  }, [id]);

  if (loading) return <div className="p-8 text-textMuted">Loading report…</div>;
  if (error) return <div className="p-8 text-error">{error}</div>;
  if (!data?.report) return <div className="p-8 text-textMuted">Report not ready yet.</div>;

  const r = data.report;
  const cb = r.category_breakdown || {};
  const ps = cb.public_speaking || { score: 0, max: 30 };
  const aq = cb.answer_quality || { score: 0, max: 40 };
  const co = cb.consistency_truthfulness || { score: 0, max: 20 };
  const fw = cb.filler_word_assessment || { score: 0, max: 10 };

  const pct = (c) => c.max ? Math.round((c.score / c.max) * 100) : 0;

  // Filler breakdown (from sub_scores)
  const fillers = Object.entries(fw.sub_scores || {})
    .filter(([k]) => k.startsWith('"'))
    .map(([k, v]) => ({ word: k.replaceAll('"',''), count: Number(v) || 0 }));

  // Radar from sub-scores of each category (normalized to 0–100)
  const radarData = [];
  const addRadar = (cat) => Object.entries(cat.sub_scores || {}).forEach(([k, v]) => {
    if (typeof v !== 'number') return;
    const maxMatch = k.match(/0-(\d+)/);
    const max = maxMatch ? Number(maxMatch[1]) : 10;
    radarData.push({ subject: k.split(' (')[0], A: Math.round((v / max) * 100) });
  });
  addRadar(ps); addRadar(aq);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="font-display font-bold text-2xl mb-1" style={{color:'#0a0a0a'}}>Interview Analysis Report</h1>
          <p className="text-textMuted text-sm">
            {data.job_title || 'Interview'} · {data.company_name || '—'} · {(data.completed_at || '').slice(0, 10)}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="badge-success">Grade {r.grade}</div>
          <button className="btn-ghost text-sm px-3 py-2 flex items-center gap-1.5" onClick={() => navigate('/dashboard')}>Back</button>
        </div>
      </div>

      {/* Score rings */}
      <motion.div initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} className="card">
        <div className="flex flex-wrap gap-8 justify-around items-center py-2">
          <ScoreRing score={pct(ps)} label={`Public Speaking (${ps.score}/${ps.max})`} color="#6366F1" />
          <ScoreRing score={pct(aq)} label={`Answer Quality (${aq.score}/${aq.max})`} color="#22D3EE" />
          <ScoreRing score={pct(co)} label={`Consistency (${co.score}/${co.max})`} color="#F59E0B" />
          <ScoreRing score={pct(fw)} label={`Filler Words (${fw.score}/${fw.max})`} color="#10B981" />
          <ScoreRing score={r.total_score} label="HireScore™" color="#8B5CF6" />
        </div>
      </motion.div>

      {/* Executive summary */}
      <motion.div initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} transition={{delay:0.1}} className="card">
        <h3 className="font-display font-semibold mb-2">🧠 Executive Summary</h3>
        <p className="text-textMuted text-sm leading-relaxed">{r.executive_summary}</p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Category breakdown with sub-scores */}
        <div className="lg:col-span-2 card">
          <h3 className="font-display font-semibold mb-4 flex items-center gap-2"><Target className="w-4 h-4 text-accent" />Category Breakdown</h3>
          <div className="space-y-4">
            {[
              { name: 'Public Speaking', c: ps, color: '#6366F1' },
              { name: 'Answer Quality', c: aq, color: '#22D3EE' },
              { name: 'Consistency & Truthfulness', c: co, color: '#F59E0B' },
              { name: 'Filler Word Assessment', c: fw, color: '#10B981' },
            ].map((row, i) => (
              <div key={i} className="p-4 rounded-xl" style={{background:'rgba(255,255,255,0.03)',border:'1px solid rgba(255,255,255,0.06)'}}>
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium" style={{color:'#0a0a0a'}}>{row.name}</span>
                  <span className="text-sm font-bold" style={{color:row.color}}>{row.c.score}/{row.c.max}</span>
                </div>
                <div className="progress-bar mb-2"><div className="progress-fill" style={{width:`${pct(row.c)}%`,background:row.color}} /></div>
                <p className="text-textMuted text-xs">{row.c.justification}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Filler words */}
        <div className="card">
          <h3 className="font-display font-semibold mb-4 flex items-center gap-2"><MessageSquare className="w-4 h-4 text-secondary" />Filler Words</h3>
          <div className="h-52">
            {fillers.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={fillers} layout="vertical" margin={{top:0,right:15,left:10,bottom:0}}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                  <XAxis type="number" hide />
                  <YAxis dataKey="word" type="category" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip cursor={{fill:'rgba(255,255,255,0.03)'}} contentStyle={{background:'#0F1628',border:'1px solid rgba(255,255,255,0.08)',borderRadius:8,fontSize:12}} />
                  <Bar dataKey="count" radius={[0,4,4,0]} barSize={20}>
                    {fillers.map((_,i)=><Cell key={i} fill={i===0?'#EF4444':'#6366F1'} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : <p className="text-textMuted text-sm">No significant filler words detected.</p>}
          </div>
          <p className="text-xs text-textMuted mt-2">
            {fw.sub_scores?.['Total Filler Count'] ?? 0} total · {fw.sub_scores?.['Filler Rate (per min)'] ?? 0}/min
          </p>
        </div>

        {/* Radar */}
        <div className="lg:col-span-1 card">
          <h3 className="font-display font-semibold mb-4 flex items-center gap-2">Skill Radar</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.08)" />
                <PolarAngleAxis dataKey="subject" tick={{fill:'#475569',fontSize:10}} />
                <Radar name="Score" dataKey="A" stroke="#6366F1" fill="#6366F1" fillOpacity={0.2} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Strengths */}
        <div className="card">
          <h3 className="font-display font-semibold mb-3 flex items-center gap-2">✅ Strengths</h3>
          <div className="space-y-2">
            {(r.strengths || []).map((s, i) => (
              <div key={i} className="p-3 rounded-xl text-sm text-success" style={{background:'rgba(16,185,129,0.06)',border:'1px solid rgba(16,185,129,0.15)'}}>{s}</div>
            ))}
          </div>
        </div>

        {/* Improvement areas */}
        <div className="card">
          <h3 className="font-display font-semibold mb-3 flex items-center gap-2"><ShieldAlert className="w-4 h-4 text-error" />Areas for Improvement</h3>
          <div className="space-y-2">
            {(r.areas_for_improvement || []).map((a, i) => (
              <div key={i} className="p-3 rounded-xl text-sm text-warning" style={{background:'rgba(245,158,11,0.06)',border:'1px solid rgba(245,158,11,0.15)'}}>{a}</div>
            ))}
          </div>
        </div>

        {/* Coaching tips */}
        <div className="lg:col-span-3 rounded-2xl p-6" style={{background:'linear-gradient(135deg,rgba(99,102,241,0.08),rgba(139,92,246,0.08))',border:'1px solid rgba(99,102,241,0.2)'}}>
          <h3 className="font-display font-semibold mb-1 flex items-center gap-2"><Lightbulb className="w-5 h-5 text-primary" />Coaching Tips</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            {(data.coaching?.tips || []).map((t, i) => (
              <div key={i} className="flex gap-3">
                <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 font-bold text-xs" style={{background:'rgba(99,102,241,0.2)',color:'#818CF8'}}>{i+1}</div>
                <div>
                  <p className="text-sm font-medium" style={{color:'#0a0a0a'}}>{t.area}</p>
                  <p className="text-textMuted text-sm">{t.tip}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
export default Results;
