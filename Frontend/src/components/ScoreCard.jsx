const ScoreCard = ({ title, score, icon: Icon, color }) => (
  <div className="card flex items-center gap-4">
    <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{background:`${color}18`}}>
      <Icon className="w-5 h-5" style={{color}} />
    </div>
    <div>
      <p className="font-display font-bold text-white text-2xl">{score}</p>
      <p className="text-textMuted text-xs">{title}</p>
    </div>
  </div>
);
export default ScoreCard;
