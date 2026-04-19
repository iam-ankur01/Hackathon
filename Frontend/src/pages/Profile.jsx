import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { User, Mail, Briefcase, Github, Linkedin, FileText, Phone, MapPin, Edit2, Save, Plus } from 'lucide-react';
import { getMe, updateProfile, uploadResume, saveSession } from '../lib/api';

// Declared at module scope so React does NOT remount the <input> on every
// keystroke (which was killing focus and silently dropping typed chars —
// that's why GitHub / LinkedIn fields appeared to "not save").
const Field = ({ label, icon: Icon, field, type = 'text', placeholder, form, setForm, edit }) => (
  <div>
    <label className="text-xs font-semibold text-textMuted uppercase tracking-wide mb-1.5 block">{label}</label>
    <div className="relative">
      <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textMuted" />
      <input
        type={type}
        className={`input-field pl-10 text-sm ${!edit ? 'opacity-70 cursor-default' : ''}`}
        value={form[field] ?? ''}
        onChange={(e) => setForm({ ...form, [field]: e.target.value })}
        readOnly={!edit}
        placeholder={placeholder}
      />
    </div>
  </div>
);

const Profile = ({ user, setUser }) => {
  const [edit, setEdit] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    name: user?.name || '',
    email: user?.email || '',
    phone: user?.phone || '',
    location: user?.location || '',
    role: user?.role || '',
    level: user?.level || '',
    college: user?.college || '',
    github: user?.github || '',
    linkedin: user?.linkedin || '',
    gmail: user?.gmail || user?.email || '',
    skills: user?.skills || '',
    bio: user?.bio || '',
  });

  useEffect(() => {
    getMe().then((u) => {
      setForm((f) => ({ ...f, ...u }));
      setUser && setUser(u);
    }).catch(() => {});
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      const { email, ...patch } = form; // email is immutable
      const updated = await updateProfile(patch);
      setUser && setUser(updated);
      const token = localStorage.getItem('hs_token');
      if (token) saveSession({ access_token: token, user: updated });
      setEdit(false);
    } finally { setSaving(false); }
  };

  const onResumeChange = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    try { await uploadResume(f); } catch {}
  };

  const fieldProps = { form, setForm, edit };

  const hirescore = Math.round(user?.hirescore || form?.hirescore || 0);
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (hirescore / 100) * circumference;

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="font-display font-bold text-2xl text-textMain">My Profile</h1>
        {!edit
          ? <button onClick={()=>setEdit(true)} className="btn-ghost text-sm px-4 py-2 flex items-center gap-2"><Edit2 className="w-3.5 h-3.5" />Edit Profile</button>
          : <button onClick={save} disabled={saving} className="btn-primary text-sm px-4 py-2 flex items-center gap-2"><Save className="w-3.5 h-3.5" />{saving ? 'Saving…' : 'Save Changes'}</button>}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left - avatar + score */}
        <div className="space-y-5">
          <motion.div initial={{opacity:0}} animate={{opacity:1}} className="card flex flex-col items-center text-center py-8">
            <div className="w-20 h-20 rounded-2xl flex items-center justify-center text-3xl font-display font-bold text-white mb-4" style={{background:'linear-gradient(135deg,#6366F1,#8B5CF6)'}}>
              {form.name?.charAt(0)}
            </div>
            <h2 className="font-display font-bold text-textMain text-lg">{form.name}</h2>
            <p className="text-textMuted text-sm">{form.role}</p>
            <p className="text-textMuted text-xs mt-0.5">{form.college}</p>
            <div className="mt-5 relative">
              <svg className="w-28 h-28 -rotate-90" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="54" fill="none" stroke="rgba(10,10,10,0.08)" strokeWidth="8" />
                <circle cx="60" cy="60" r="54" fill="none" stroke="url(#grad)" strokeWidth="8" strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round" />
                <defs>
                  <linearGradient id="grad" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="#6366F1" />
                    <stop offset="100%" stopColor="#22D3EE" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="font-display font-bold text-2xl text-textMain">{hirescore}</span>
                <span className="text-textMuted text-xs">HireScore™</span>
              </div>
            </div>
            <p className="text-xs text-textMuted mt-2">+8 points this week</p>
          </motion.div>

          <div className="card">
            <h3 className="text-sm font-semibold text-textMain mb-3">Quick Links</h3>
            <div className="space-y-2">
              {[{icon:Github,label:'GitHub',val:form.github},{icon:Linkedin,label:'LinkedIn',val:form.linkedin}].map((l,i)=>(
                <a key={i} href={`https://${l.val}`} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-sm text-textMuted hover:text-primary p-2 rounded-lg hover:bg-surfaceHigh transition-all">
                  <l.icon className="w-4 h-4" /><span className="truncate">{l.val}</span>
                </a>
              ))}
            </div>
          </div>
        </div>

        {/* Right - form */}
        <div className="lg:col-span-2 space-y-5">
          <div className="card space-y-4">
            <h3 className="font-semibold text-textMain text-sm uppercase tracking-wide">Personal Information</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field {...fieldProps} label="Full Name" icon={User} field="name" />
              <Field {...fieldProps} label="Email" icon={Mail} field="email" type="email" />
              <Field {...fieldProps} label="Phone" icon={Phone} field="phone" />
              <Field {...fieldProps} label="Location" icon={MapPin} field="location" />
              <Field {...fieldProps} label="Target Role" icon={Briefcase} field="role" />
              <Field {...fieldProps} label="College / Company" icon={FileText} field="college" />
            </div>
            <div>
              <label className="text-xs font-semibold text-textMuted uppercase tracking-wide mb-1.5 block">Bio</label>
              <textarea className={`input-field text-sm h-20 resize-none ${!edit?'opacity-70 cursor-default':''}`} value={form.bio} onChange={e=>setForm({...form,bio:e.target.value})} readOnly={!edit} />
            </div>
          </div>

          <div className="card space-y-4">
            <h3 className="font-semibold text-textMain text-sm uppercase tracking-wide">Profile Links & Documents</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field {...fieldProps} label="GitHub Username" icon={Github} field="github" placeholder="github.com/username" />
              <Field {...fieldProps} label="LinkedIn Profile" icon={Linkedin} field="linkedin" placeholder="linkedin.com/in/..." />
              <Field {...fieldProps} label="Gmail" icon={Mail} field="gmail" placeholder="you@gmail.com" />
            </div>
            <div>
              <label className="text-xs font-semibold text-textMuted uppercase tracking-wide mb-2 block">Resume</label>
              <div className="flex items-center gap-3 p-4 rounded-xl" style={{background:'rgba(10,10,10,0.03)',border:'1px dashed rgba(10,10,10,0.15)'}}>
                <FileText className="w-5 h-5 text-primary" />
                <div className="flex-1">
                  <p className="text-textMain text-sm font-medium">Onkar_Kulkarni_Resume.pdf</p>
                  <p className="text-textMuted text-xs">Uploaded Apr 10, 2026 · 284 KB</p>
                </div>
                {edit && <label htmlFor="newResume" className="tag cursor-pointer hover:bg-primary/20 transition-all text-xs"><Plus className="w-3 h-3 inline" /> Update<input id="newResume" type="file" className="hidden" accept=".pdf,.doc,.docx" onChange={onResumeChange} /></label>}
              </div>
            </div>
          </div>

          <div className="card">
            <h3 className="font-semibold text-textMain text-sm uppercase tracking-wide mb-3">Skills</h3>
            {edit
              ? <input className="input-field text-sm" value={form.skills} onChange={e=>setForm({...form,skills:e.target.value})} placeholder="Add skills separated by commas" />
              : <div className="flex flex-wrap gap-2">{form.skills.split(',').map((s,i)=><span key={i} className="tag">{s.trim()}</span>)}</div>
            }
          </div>
        </div>
      </div>
    </div>
  );
};
export default Profile;
