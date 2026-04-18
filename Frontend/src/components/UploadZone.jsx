import { useRef, useState } from 'react';
import { Upload, CheckCircle } from 'lucide-react';
const UploadZone = ({ onFileSelect }) => {
  const [file, setFile] = useState(null);
  const ref = useRef();
  const handle = (f) => { setFile(f); onFileSelect(f); };
  return !file ? (
    <div onClick={()=>ref.current.click()} className="border-2 border-dashed border-white/10 rounded-2xl p-10 text-center cursor-pointer hover:border-primary/40 hover:bg-white/2 transition-all">
      <input ref={ref} type="file" className="hidden" accept="video/*,audio/*" onChange={e=>handle(e.target.files[0])} />
      <Upload className="w-8 h-8 mx-auto mb-3 text-textMuted" />
      <p className="text-white text-sm font-medium">Drop file or click to upload</p>
    </div>
  ) : (
    <div className="flex items-center gap-3 p-4 rounded-xl" style={{background:'rgba(16,185,129,0.08)',border:'1px solid rgba(16,185,129,0.2)'}}>
      <CheckCircle className="w-5 h-5 text-success" />
      <p className="text-white text-sm font-medium truncate">{file.name}</p>
    </div>
  );
};
export default UploadZone;
