import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';
const LoadingState = () => (
  <div className="text-center">
    <div className="w-16 h-16 mx-auto mb-6 rounded-2xl flex items-center justify-center" style={{background:'rgba(99,102,241,0.1)',border:'1px solid rgba(99,102,241,0.2)'}}>
      <Sparkles className="w-8 h-8 text-primary animate-pulse" />
    </div>
    <p className="font-display font-bold text-white text-xl mb-2">Analyzing...</p>
    <p className="text-textMuted text-sm">Processing your interview</p>
  </div>
);
export default LoadingState;
