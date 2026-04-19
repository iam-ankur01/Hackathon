import { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { History as HistoryIcon, Search, FileText, Download, Trash2, ChevronDown, ChevronUp, Mic, Video, FileDigit } from 'lucide-react';
import { listHistory, deleteHistoryEntry } from '../lib/api';
import { jsPDF } from 'jspdf';
import { Document, Packer, Paragraph, HeadingLevel, TextRun } from 'docx';
import { saveAs } from 'file-saver';

const KindIcon = ({ kind }) => {
  if (kind === 'video') return <Video className="w-4 h-4" />;
  if (kind === 'transcript') return <FileDigit className="w-4 h-4" />;
  return <Mic className="w-4 h-4" />;
};

const formatDate = (iso) => {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, { year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' });
  } catch {
    return iso;
  }
};

const baseName = (fn) => (fn || 'transcript').replace(/\.[^.]+$/, '');

const downloadPDF = (row) => {
  const doc = new jsPDF({ unit: 'pt', format: 'letter' });
  const margin = 48;
  const pageW = doc.internal.pageSize.getWidth();
  const pageH = doc.internal.pageSize.getHeight();
  const maxWidth = pageW - margin * 2;

  doc.setFontSize(16);
  doc.text('Interview Transcript', margin, margin);
  doc.setFontSize(10);
  doc.setTextColor(110);
  doc.text(`File: ${row.filename}`, margin, margin + 20);
  doc.text(`Saved: ${formatDate(row.created_at)}`, margin, margin + 34);
  if (row.job_title || row.company_name) {
    doc.text(`Role: ${[row.job_title, row.company_name].filter(Boolean).join(' @ ')}`, margin, margin + 48);
  }

  doc.setTextColor(20);
  doc.setFontSize(11);
  const body = row.transcript || '(transcript not available)';
  const lines = doc.splitTextToSize(body, maxWidth);
  let y = margin + 72;
  for (const line of lines) {
    if (y > pageH - margin) {
      doc.addPage();
      y = margin;
    }
    doc.text(line, margin, y);
    y += 14;
  }
  doc.save(`${baseName(row.filename)}-transcript.pdf`);
};

const downloadDOCX = async (row) => {
  const body = row.transcript || '(transcript not available)';
  const doc = new Document({
    sections: [{
      properties: {},
      children: [
        new Paragraph({ text: 'Interview Transcript', heading: HeadingLevel.HEADING_1 }),
        new Paragraph({ children: [new TextRun({ text: `File: ${row.filename}`, italics: true })] }),
        new Paragraph({ children: [new TextRun({ text: `Saved: ${formatDate(row.created_at)}`, italics: true })] }),
        ...(row.job_title || row.company_name
          ? [new Paragraph({ children: [new TextRun({ text: `Role: ${[row.job_title, row.company_name].filter(Boolean).join(' @ ')}`, italics: true })] })]
          : []),
        new Paragraph({ text: '' }),
        ...body.split(/\n\n+/).map(para => new Paragraph({ children: [new TextRun(para)] })),
      ],
    }],
  });
  const blob = await Packer.toBlob(doc);
  saveAs(blob, `${baseName(row.filename)}-transcript.docx`);
};

const History = () => {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [q, setQ] = useState('');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [expanded, setExpanded] = useState(null);

  const load = () => {
    setLoading(true);
    setError('');
    listHistory()
      .then((data) => setRows(Array.isArray(data) ? data : []))
      .catch((e) => setError(e?.response?.data?.detail || 'Could not load history.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const filtered = useMemo(() => {
    const ql = q.trim().toLowerCase();
    return rows.filter((r) => {
      if (ql) {
        const hay = `${r.filename} ${r.job_title} ${r.company_name}`.toLowerCase();
        if (!hay.includes(ql)) return false;
      }
      if (from) {
        if ((r.created_at || '') < from) return false;
      }
      if (to) {
        // add a day so the 'to' date is inclusive
        if ((r.created_at || '').slice(0, 10) > to) return false;
      }
      return true;
    });
  }, [rows, q, from, to]);

  const remove = async (id) => {
    if (!window.confirm('Delete this history entry? This also removes the interview analysis.')) return;
    try {
      await deleteHistoryEntry(id);
      setRows(prev => prev.filter(r => r.id !== id));
      if (expanded === id) setExpanded(null);
    } catch (e) {
      setError('Delete failed.');
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-5">
      <div className="flex items-center gap-2">
        <HistoryIcon className="w-5 h-5 text-primary" />
        <h1 className="font-display font-bold text-2xl text-white">History</h1>
      </div>
      <p className="text-textMuted text-sm">
        Every interview you upload or record is saved here with its full transcript.
        Export any entry as PDF or Word.
      </p>

      {/* Filters */}
      <div className="card flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-textMuted" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search by filename, role, or company…"
            className="w-full pl-9 pr-3 py-2 rounded-lg text-sm text-white outline-none"
            style={{ background: 'rgba(15,22,40,0.9)', border: '1px solid rgba(255,255,255,0.08)' }}
          />
        </div>
        <div className="flex items-center gap-2 text-xs text-textMuted">
          <span>From</span>
          <input
            type="date"
            value={from}
            onChange={(e) => setFrom(e.target.value)}
            className="px-2 py-1.5 rounded-lg text-white text-xs outline-none"
            style={{ background: 'rgba(15,22,40,0.9)', border: '1px solid rgba(255,255,255,0.08)' }}
          />
          <span>To</span>
          <input
            type="date"
            value={to}
            onChange={(e) => setTo(e.target.value)}
            className="px-2 py-1.5 rounded-lg text-white text-xs outline-none"
            style={{ background: 'rgba(15,22,40,0.9)', border: '1px solid rgba(255,255,255,0.08)' }}
          />
          {(q || from || to) && (
            <button onClick={() => { setQ(''); setFrom(''); setTo(''); }} className="text-primary-light hover:underline">
              clear
            </button>
          )}
        </div>
      </div>

      {error && <div className="card text-red-400 text-sm">{error}</div>}
      {loading && <div className="card text-textMuted text-sm">Loading your history…</div>}
      {!loading && filtered.length === 0 && (
        <div className="card text-center py-10 text-textMuted text-sm">
          {rows.length === 0
            ? 'No entries yet — upload or record an interview to get started.'
            : 'No entries match your filters.'}
        </div>
      )}

      {/* Rows */}
      <div className="space-y-2">
        <AnimatePresence initial={false}>
          {filtered.map((r) => {
            const isOpen = expanded === r.id;
            return (
              <motion.div
                key={r.id}
                layout
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="card"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 text-primary-light"
                       style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)' }}>
                    <KindIcon kind={r.file_kind} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm font-medium truncate">{r.filename}</p>
                    <p className="text-textMuted text-xs">
                      {formatDate(r.created_at)}
                      {r.job_title ? ` · ${r.job_title}` : ''}
                      {r.company_name ? ` @ ${r.company_name}` : ''}
                      {typeof r.total_score === 'number' ? ` · ${Math.round(r.total_score)}/100 (${r.grade || '—'})` : ''}
                    </p>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => downloadPDF(r)}
                      disabled={!r.transcript_available}
                      title="Download transcript as PDF"
                      className="p-2 rounded-lg text-textMuted hover:text-white hover:bg-white/5 disabled:opacity-40"
                    >
                      <Download className="w-4 h-4" /><span className="sr-only">PDF</span>
                    </button>
                    <button
                      onClick={() => downloadDOCX(r)}
                      disabled={!r.transcript_available}
                      title="Download transcript as Word (.docx)"
                      className="p-2 rounded-lg text-textMuted hover:text-white hover:bg-white/5 disabled:opacity-40"
                    >
                      <FileText className="w-4 h-4" /><span className="sr-only">DOCX</span>
                    </button>
                    <button
                      onClick={() => setExpanded(isOpen ? null : r.id)}
                      title={isOpen ? 'Collapse' : 'Preview transcript'}
                      className="p-2 rounded-lg text-textMuted hover:text-white hover:bg-white/5"
                    >
                      {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                    <button
                      onClick={() => remove(r.id)}
                      title="Delete entry"
                      className="p-2 rounded-lg text-textMuted hover:text-red-400 hover:bg-red-500/5"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {isOpen && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-3 pt-3 border-t border-white/5"
                  >
                    {r.transcript_available ? (
                      <>
                        <p className="text-xs text-textMuted mb-2">{r.transcript_word_count} words</p>
                        <pre className="text-xs text-textMain whitespace-pre-wrap leading-relaxed max-h-80 overflow-y-auto"
                             style={{ fontFamily: 'inherit' }}>
                          {r.transcript}
                        </pre>
                      </>
                    ) : (
                      <p className="text-xs text-textMuted">
                        {r.status === 'processing'
                          ? 'Transcript will appear here once analysis finishes.'
                          : 'Transcript not available for this entry.'}
                      </p>
                    )}
                  </motion.div>
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default History;
