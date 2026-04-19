import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Circle, Map, Calendar, Target, Sparkles } from 'lucide-react';
import { getRoadmap, saveRoadmapPreferences, getMe } from '../lib/api';

const PHASE_COLORS = ['#22D3EE', '#6366F1', '#8B5CF6', '#F59E0B', '#10B981', '#EC4899'];

const chunkByWeek = (days) => {
  const weeks = [];
  for (let i = 0; i < days.length; i += 7) {
    weeks.push(days.slice(i, i + 7));
  }
  return weeks;
};

const Roadmap = () => {
  const [days, setDays] = useState(30);
  const [pendingDays, setPendingDays] = useState(30);
  const [plan, setPlan] = useState(null);
  const [taskStates, setTaskStates] = useState({}); // { "day-taskIdx": true }
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadRoadmap = (d) => {
    setLoading(true);
    setError('');
    getRoadmap(d)
      .then((r) => {
        setPlan(r);
        if (r.days_requested) setDays(r.days_requested);
      })
      .catch(() => setError('Could not load your roadmap. Try again.'))
      .finally(() => setLoading(false));
  };

  // On mount: read saved preference, then fetch roadmap.
  useEffect(() => {
    getMe()
      .then((u) => {
        const saved = u?.roadmap_days && Number(u.roadmap_days) > 0 ? Number(u.roadmap_days) : 30;
        setDays(saved);
        setPendingDays(saved);
        loadRoadmap(saved);
      })
      .catch(() => loadRoadmap(30));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleGenerate = async () => {
    const n = Math.max(1, Math.min(180, parseInt(pendingDays, 10) || 30));
    setPendingDays(n);
    try {
      await saveRoadmapPreferences(n);
    } catch {
      // non-fatal: still attempt to render the plan
    }
    setTaskStates({});
    loadRoadmap(n);
  };

  const toggle = (dayNum, taskIdx) => {
    const key = `${dayNum}-${taskIdx}`;
    setTaskStates((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const planDays = plan?.days || [];
  const allTasks = planDays.flatMap((d, di) => (d.tasks || []).map((_, ti) => `${d.day}-${ti}`));
  const doneCount = allTasks.filter((k) => taskStates[k]).length;
  const totalTasks = allTasks.length;
  const weeks = chunkByWeek(planDays);

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display font-bold text-2xl text-textMain mb-1 flex items-center gap-2">
            <Map className="w-5 h-5 text-primary" />Your Personalized Roadmap
          </h1>
          <p className="text-textMuted text-sm">
            Aligned with the weaknesses from your latest interview analysis.
          </p>
        </div>
        {totalTasks > 0 && (
          <div className="text-right">
            <p className="text-3xl font-display font-bold text-textMain">
              {doneCount}<span className="text-textMuted text-lg">/{totalTasks}</span>
            </p>
            <p className="text-xs text-textMuted">tasks complete</p>
          </div>
        )}
      </div>

      {/* Days-to-prepare prompt */}
      <div className="card">
        <div className="flex items-start gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
               style={{background:'linear-gradient(135deg,#6366F1,#22D3EE)'}}>
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="text-textMain font-semibold">
              How many days do you want to prepare for your next interview?
            </p>
            <p className="text-textMuted text-xs mt-1">
              Your plan will be distributed across that many days, ramping from diagnostics
              to mock practice. Range: 1–180.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <input
            type="number"
            min={1}
            max={180}
            value={pendingDays}
            onChange={(e) => setPendingDays(e.target.value)}
            className="input-field w-28 text-sm py-2"
          />
          <span className="text-textMuted text-sm">days</span>
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="ml-auto px-4 py-2 rounded-lg text-white text-sm font-medium disabled:opacity-60"
            style={{background:'linear-gradient(135deg,#6366F1,#8B5CF6)'}}
          >
            {loading ? 'Generating…' : 'Generate Roadmap'}
          </button>
        </div>
        {error && <p className="text-red-400 text-xs mt-3">{error}</p>}
      </div>

      {/* Plan summary */}
      {plan && (plan.primary_focus || plan.summary) && (
        <div className="card flex items-start gap-3">
          <Target className="w-5 h-5 text-primary-light flex-shrink-0 mt-0.5" />
          <div>
            {plan.primary_focus && (
              <p className="text-textMain text-sm font-semibold">
                Primary focus: <span className="text-primary">{plan.primary_focus}</span>
              </p>
            )}
            {plan.summary && <p className="text-textMuted text-sm mt-1">{plan.summary}</p>}
          </div>
        </div>
      )}

      {/* Overall progress bar */}
      {totalTasks > 0 && (
        <div className="card">
          <div className="flex justify-between text-xs text-textMuted mb-2">
            <span>Overall Progress</span>
            <span>{Math.round((doneCount / totalTasks) * 100)}%</span>
          </div>
          <div className="progress-bar h-2">
            <div className="progress-fill" style={{ width: `${(doneCount / totalTasks) * 100}%` }} />
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && planDays.length === 0 && (
        <div className="card text-center py-10">
          <p className="text-textMuted text-sm">
            {plan?.summary || 'No roadmap yet. Complete an interview and click Generate.'}
          </p>
        </div>
      )}

      {/* Weekly groups */}
      <div className="space-y-5">
        {weeks.map((weekDays, wi) => {
          const color = PHASE_COLORS[wi % PHASE_COLORS.length];
          const weekDone = weekDays.reduce((acc, d) => {
            const taskCount = (d.tasks || []).length;
            const doneInDay = (d.tasks || []).filter((_, ti) => taskStates[`${d.day}-${ti}`]).length;
            return { total: acc.total + taskCount, done: acc.done + doneInDay };
          }, { total: 0, done: 0 });

          return (
            <motion.div
              key={wi}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: wi * 0.08 }}
              className="card"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center font-display font-bold text-sm"
                    style={{ background: `${color}20`, border: `1px solid ${color}40`, color }}
                  >
                    W{wi + 1}
                  </div>
                  <div>
                    <p className="text-textMain font-semibold">Week {wi + 1}</p>
                    <p className="text-textMuted text-xs flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      Day {weekDays[0].day}–{weekDays[weekDays.length - 1].day}
                    </p>
                  </div>
                </div>
                <span className="text-xs font-semibold" style={{ color }}>
                  {weekDone.done}/{weekDone.total} done
                </span>
              </div>

              <div className="space-y-3">
                {weekDays.map((d) => (
                  <div key={d.day} className="rounded-xl p-3" style={{ background: 'rgba(10,10,10,0.03)', border: '1px solid rgba(10,10,10,0.05)' }}>
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-textMain text-sm font-medium">
                        Day {d.day} — <span className="text-textMuted">{d.focus_area}</span>
                      </p>
                      {d.time_estimate_minutes ? (
                        <span className="text-[11px] text-textMuted">{d.time_estimate_minutes} min</span>
                      ) : null}
                    </div>
                    <div className="space-y-1.5">
                      {(d.tasks || []).map((task, ti) => {
                        const key = `${d.day}-${ti}`;
                        const isDone = !!taskStates[key];
                        const title = typeof task === 'string' ? task : (task?.title || task?.task || '');
                        const detail = typeof task === 'string' ? '' : (task?.detail || task?.description || '');
                        return (
                          <button
                            key={ti}
                            onClick={() => toggle(d.day, ti)}
                            className="w-full flex items-start gap-2 p-2.5 rounded-lg hover:bg-surfaceHigh transition-all text-left"
                          >
                            {isDone
                              ? <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color }} />
                              : <Circle className="w-4 h-4 flex-shrink-0 mt-0.5 text-textMuted" />}
                            <div className="flex-1 min-w-0">
                              <p className={`text-xs font-medium leading-relaxed ${isDone ? 'text-textMuted line-through' : 'text-textMain'}`}>
                                {title}
                              </p>
                              {detail && (
                                <p className={`text-[11px] leading-relaxed mt-1 ${isDone ? 'text-textMuted/60 line-through' : 'text-textMuted'}`}>
                                  {detail}
                                </p>
                              )}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
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
