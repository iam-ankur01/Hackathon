const ProgressMetric = ({ label, value, max = 100, color = '#6366F1' }) => (
  <div>
    <div className="flex justify-between text-xs mb-1"><span className="text-textMuted">{label}</span><span className="text-white font-semibold">{value}%</span></div>
    <div className="progress-bar"><div className="progress-fill" style={{width:`${value/max*100}%`,background:color}} /></div>
  </div>
);
export default ProgressMetric;
