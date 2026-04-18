import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Mic, Link as LinkIcon, Briefcase, FileText, Sparkles, Video, X, CheckCircle, Clock, Zap } from 'lucide-react';
import { submitInterview, getInterview, getDashboard, uploadResume } from '../lib/api';

const UploadTab = ({ icon: Icon, label, active, onClick }) => (
  <button onClick={onClick} className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${active ? 'text-primary bg-primary/10 border border-primary/25' : 'text-textMuted hover:text-white hover:bg-white/5 border border-transparent'}`}>
    <Icon className="w-4 h-4" /> {label}
  </button>
);

const Dashboard = ({ user }) => {
  const navigate = useNavigate();
  const [tab, setTab] = useState('upload');
  const [file, setFile] = useState(null);
  const [zoomLink, setZoomLink] = useState('');
  const [jd, setJd] = useState('');
  const [role, setRole] = useState('Software Engineer');
  const [company, setCompany] = useState('');
  const [round, setRound] = useState('HR Round');
  const [loading, setLoading] = useState(false);
  const [drag, setDrag] = useState(false);
  const fileRef = useRef();

  const [error, setError] = useState('');
  const [stats, setStats] = useState(null);
  const [recentAnalyses, setRecentAnalyses] = useState([]);

  useEffect(() => {
    getDashboard().then((d) => {
      setStats(d);
      setRecentAnalyses((d.recent || []).map(r => ({
        id: r.id,
        role: r.job_title || 'Interview',
        date: (r.completed_at || '').slice(0, 10),
        score: Math.round(r.total_score || 0),
        stage: r.grade || '—',
      })));
    }).catch(() => {});
  }, []);

  const handleFile = (f) => { if (f) setFile(f); };
  const handleDrop = (e) => { e.preventDefault(); setDrag(false); handleFile(e.dataTransfer.files[0]); };
  const canAnalyze = tab === 'zoom' ? zoomLink : file;

  const handleAnalyze = async () => {
    if (!file && !jd) { setError('Please upload an audio/video file.'); return; }
    setError('');
    setLoading(true);
    try {
      const res = await submitInterview({
        file,
        job_description: jd,
        job_title: role,
        company_name: company,
      });
      // Poll until pipeline finishes (can take 30–60s)
      const interviewId = res.id;
      let tries = 0;
      const poll = async () => {
        tries++;
        try {
          const data = await getInterview(interviewId);
          if (data.status === 'completed') {
            navigate(`/results/${interviewId}`);
            return;
          }
          if (data.status === 'failed') {
            setError(`Analysis failed: ${data.error || 'unknown error'}`);
            setLoading(false);
            return;
          }
        } catch (e) { /* keep polling */ }
        if (tries < 60) setTimeout(poll, 3000);
        else { setError('Analysis is taking longer than expected. Check back later.'); setLoading(false); }
      };
      setTimeout(poll, 3000);
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Upload failed');
      setLoading(false);
    }
  };

  const handleResumePick = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    try { await uploadResume(f); } catch (err) { setError('Resume upload failed'); }
  };

  if (loading) return (
    <div className="flex-1 flex flex-col items-center justify-center h-full min-h-[calc(100vh-64px)]">
      <motion.div initial={{opacity:0,scale:0.9}} animate={{opacity:1,scale:1}} className="text-center">
        <div className="w-20 h-20 mx-auto mb-8 rounded-2xl flex items-center justify-center relative" style={{background:'rgba(99,102,241,0.1)',border:'1px solid rgba(99,102,241,0.2)'}}>
          <Sparkles className="w-10 h-10 text-primary animate-pulse" />
          <div className="absolute inset-0 rounded-2xl border-2 border-primary/40 animate-ping" />
        </div>
        <h3 className="font-display font-bold text-2xl text-white mb-2">Analyzing your interview...</h3>
        <p className="text-textMuted mb-8 text-sm">Processing audio · Detecting patterns · Mapping to role</p>
        <div className="w-64 mx-auto space-y-3">
          {['Transcribing audio','Detecting speech patterns','Evaluating STAR structure','Generating recruiter insights','Building your roadmap'].map((step,i)=>(
            <motion.div key={i} initial={{opacity:0,x:-10}} animate={{opacity:1,x:0}} transition={{delay:i*0.5}} className="flex items-center gap-3 text-sm text-textMuted">
              <motion.div initial={{scale:0}} animate={{scale:1}} transition={{delay:i*0.5+0.3}}>
                <CheckCircle className="w-4 h-4 text-success" />
              </motion.div>
              {step}
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Welcome */}
      <motion.div initial={{opacity:0,y:10}} animate={{opacity:1,y:0}}>
        <h1 className="font-display font-bold text-2xl text-white mb-0.5">Welcome back, {user?.name?.split(' ')[0] || 'Onkar'} 👋</h1>
        <p className="text-textMuted text-sm">Upload your interview recording and get a full debrief in under 60 seconds.</p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main upload card */}
        <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{delay:0.1}} className="lg:col-span-2 card space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="font-display font-semibold text-white text-lg flex items-center gap-2">
              <Video className="w-5 h-5 text-primary" /> New Analysis
            </h2>
          </div>

          {/* Upload tabs */}
          <div className="flex gap-2 flex-wrap">
            <UploadTab icon={Upload} label="Upload File" active={tab==='upload'} onClick={()=>setTab('upload')} />
            <UploadTab icon={Mic} label="Record Audio" active={tab==='record'} onClick={()=>setTab('record')} />
            <UploadTab icon={LinkIcon} label="Zoom Link" active={tab==='zoom'} onClick={()=>setTab('zoom')} />
          </div>

          <AnimatePresence mode="wait">
            {tab === 'upload' && (
              <motion.div key="upload" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}>
                {!file ? (
                  <div
                    onDrop={handleDrop} onDragOver={e=>{e.preventDefault();setDrag(true)}} onDragLeave={()=>setDrag(false)}
                    onClick={()=>fileRef.current.click()}
                    className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all ${drag ? 'border-primary bg-primary/5' : 'border-white/10 hover:border-primary/40 hover:bg-white/2'}`}
                  >
                    <input ref={fileRef} type="file" className="hidden" accept="video/*,audio/*" onChange={e=>handleFile(e.target.files[0])} />
                    <Upload className="w-10 h-10 mx-auto mb-3 text-textMuted" />
                    <p className="text-white font-medium mb-1">Drop your interview recording here</p>
                    <p className="text-textMuted text-sm">MP4, MOV, WebM, MP3, WAV · Max 500MB</p>
                  </div>
                ) : (
                  <div className="flex items-center gap-3 p-4 rounded-xl" style={{background:'rgba(16,185,129,0.08)',border:'1px solid rgba(16,185,129,0.2)'}}>
                    <CheckCircle className="w-5 h-5 text-success flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-white text-sm font-medium truncate">{file.name}</p>
                      <p className="text-textMuted text-xs">{(file.size/1024/1024).toFixed(1)} MB</p>
                    </div>
                    <button onClick={()=>setFile(null)} className="text-textMuted hover:text-white"><X className="w-4 h-4" /></button>
                  </div>
                )}
              </motion.div>
            )}
            {tab === 'record' && (
              <motion.div key="record" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="text-center py-10 border-2 border-dashed border-white/10 rounded-2xl">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center cursor-pointer hover:scale-105 transition-transform" style={{background:'rgba(239,68,68,0.15)',border:'2px solid rgba(239,68,68,0.4)'}}>
                  <Mic className="w-7 h-7 text-error" />
                </div>
                <p className="text-white font-medium mb-1">Click to start recording</p>
                <p className="text-textMuted text-sm">Record your mock interview directly in the browser</p>
              </motion.div>
            )}
            {tab === 'zoom' && (
              <motion.div key="zoom" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}>
                <input className="input-field" placeholder="Paste your Zoom cloud recording link here..." value={zoomLink} onChange={e=>setZoomLink(e.target.value)} />
                <p className="text-textMuted text-xs mt-2">We'll automatically extract and analyze the audio from the recording</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Job context */}
          <div className="space-y-3 pt-1 border-t border-white/5">
            <p className="text-xs font-semibold text-textMuted uppercase tracking-wide">Interview Context</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-textMuted mb-1 block">Target Role</label>
                <div className="relative">
                  <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textMuted" />
                  <select className="input-field pl-9 appearance-none text-sm" value={role} onChange={e=>setRole(e.target.value)}>
                    {['Software Engineer','Data Scientist','Product Manager','Business Analyst','DevOps','Marketing','Sales','HR'].map(r=><option key={r}>{r}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="text-xs text-textMuted mb-1 block">Company Name</label>
                <input className="input-field text-sm" placeholder="e.g. TCS, Infosys, Google..." value={company} onChange={e=>setCompany(e.target.value)} />
              </div>
              <div>
                <label className="text-xs text-textMuted mb-1 block">Interview Round</label>
                <select className="input-field text-sm appearance-none" value={round} onChange={e=>setRound(e.target.value)}>
                  {['HR Round','Technical Round','System Design','Behavioral','Case Study','Managerial'].map(r=><option key={r}>{r}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-textMuted mb-1 block">Resume (optional)</label>
                <div className="relative">
                  <FileText className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textMuted" />
                  <input type="file" className="hidden" id="resumeUpload" accept=".pdf,.doc,.docx" onChange={handleResumePick} />
                  <label htmlFor="resumeUpload" className="input-field pl-9 text-sm cursor-pointer block text-textMuted">Upload PDF / DOCX</label>
                </div>
              </div>
            </div>
          </div>

          {/* JD */}
          <div>
            <label className="text-xs text-textMuted mb-1 block">Job Description (paste for better role-matching)</label>
            <textarea className="input-field text-sm h-28 resize-none" placeholder="Paste the job description here — we'll map your answers against the actual role requirements..." value={jd} onChange={e=>setJd(e.target.value)} />
          </div>

          {error && <p className="text-error text-sm">{error}</p>}
          <button onClick={handleAnalyze} disabled={!file} className={`btn-primary w-full flex items-center justify-center gap-2 py-3.5 ${(!file) ? 'opacity-50 cursor-not-allowed' : ''}`}>
            <Sparkles className="w-5 h-5" /> Analyze Interview
          </button>
        </motion.div>

        {/* Right sidebar */}
        <div className="space-y-5">
          {/* Quick stats */}
          <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{delay:0.2}} className="card">
            <h3 className="font-semibold text-white text-sm mb-4 flex items-center gap-2"><Zap className="w-4 h-4 text-accent" />Quick Stats</h3>
            <div className="space-y-3">
              {[
                {label:'Interviews analyzed', val: String(stats?.total_interviews ?? 0)},
                {label:'HireScore™', val: String(stats?.hirescore ?? 0)},
                {label:'Latest score', val: stats?.latest_score != null ? String(Math.round(stats.latest_score)) : '—'},
                {label:'Latest grade', val: stats?.latest_grade || '—'},
              ].map((s,i)=>(
                <div key={i} className="flex justify-between text-sm">
                  <span className="text-textMuted">{s.label}</span>
                  <span className="text-white font-medium">{s.val}</span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Recent */}
          <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{delay:0.3}} className="card">
            <h3 className="font-semibold text-white text-sm mb-4 flex items-center gap-2"><Clock className="w-4 h-4 text-primary" />Recent Analyses</h3>
            <div className="space-y-3">
              {recentAnalyses.length === 0 && <p className="text-textMuted text-xs">No analyses yet — upload your first interview.</p>}
              {recentAnalyses.map((a,i)=>(
                <div key={i} onClick={()=>a.id && navigate(`/results/${a.id}`)} className="flex items-center gap-3 p-3 rounded-xl hover:bg-white/3 cursor-pointer transition-all border border-transparent hover:border-white/5">
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 font-display font-bold text-sm" style={{background:'rgba(99,102,241,0.12)',color:'#818CF8'}}>{a.score}</div>
                  <div className="min-w-0 flex-1">
                    <p className="text-white text-xs font-medium truncate">{a.role}</p>
                    <p className="text-textMuted text-xs">{a.stage} · {a.date}</p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};
export default Dashboard;
