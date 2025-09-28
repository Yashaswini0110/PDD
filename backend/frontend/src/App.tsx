import { useState, useEffect, useMemo } from 'react'
import './App.css'
import { uploadPdf, analyze, ask, exportReportUrl, deleteNow } from '@/lib/api'

// --- Type Definitions ---
interface Flag {
  clause_id: number;
  evidence: string;
  reason: string;
  severity: "Low" | "Medium" | "High" | "Info" | "Error" | "Unknown";
  negotiation_hint?: string | null;
}

interface QaResult {
  answer: string;
  source_clause: {
    id: number;
    text: string;
  } | null;
}

interface Score {
  value: number;
  level: 'Good' | 'Fair' | 'Poor';
  color: string;
}

function App() {
  const [objectName, setObjectName] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [flags, setFlags] = useState<Flag[]>([]);
  const [clauses, setClauses] = useState<any[]>([]); // Keep track of total clauses for scoring
  const [q, setQ] = useState('');
  const [qaResult, setQaResult] = useState<QaResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<string>('');

  // --- Timer for Auto-Delete ---
  useEffect(() => {
    if (!expiresAt) {
      setTimeRemaining('');
      return;
    }
    
    const interval = setInterval(() => {
      const now = new Date();
      const expires = new Date(expiresAt);
      const diff = expires.getTime() - now.getTime();
      
      if (diff <= 0) {
        setTimeRemaining('Expired');
        clearInterval(interval);
        setObjectName(null);
        setExpiresAt(null);
      } else {
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        setTimeRemaining(`${hours}h ${minutes}m remaining`);
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }, [expiresAt]);

  // --- Overall Scoring System ---
  const overallScore = useMemo<Score | null>(() => {
    if (!flags.length || !clauses.length) return null;

    const riskTotal = flags.reduce((acc, flag) => {
      if (flag.severity === 'High') return acc + 10;
      if (flag.severity === 'Medium') return acc + 5;
      if (flag.severity === 'Low') return acc + 1;
      return acc;
    }, 0);

    const maxRisk = clauses.length * 10; // Assume worst case is every clause is high risk
    const safetyScore = Math.round(Math.max(0, (1 - (riskTotal / maxRisk))) * 100);

    if (safetyScore >= 85) {
      return { value: safetyScore, level: 'Good', color: '#16a34a' };
    }
    if (safetyScore >= 60) {
      return { value: safetyScore, level: 'Fair', color: '#f59e0b' };
    }
    return { value: safetyScore, level: 'Poor', color: '#dc2626' };
  }, [flags, clauses]);


  // --- API Handlers ---
  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setError(null);
    setUploading(true);
    setFlags([]);
    setQaResult(null);
    try {
      const res = await uploadPdf(f);
      setObjectName(res.object_name);
      setExpiresAt(res.expires_at);
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || 'Upload failed';
      setError(errorDetail);
    } finally {
      setUploading(false);
    }
  }

  async function onDelete() {
    if (!objectName) return;
    setError(null);
    setFlags([]);
    setQaResult(null);
    try {
      await deleteNow(objectName);
      setObjectName(null);
      setExpiresAt(null);
    } catch (err: any) {
      setError(err?.message || 'Delete failed');
    }
  }

  async function onAnalyze() {
    if (!objectName) return;
    setAnalyzing(true);
    setError(null);
    try {
      const res = await analyze(objectName);
      setClauses(res.clauses || []); // Store clauses for scoring
      setFlags(res.flags || []);
    } catch (err: any) {
      setError(err?.message || 'Analyze failed');
    } finally {
      setAnalyzing(false);
    }
  }

  async function onAsk() {
    if (!objectName || !q) return;
    setError(null);
    try {
      const res = await ask(objectName, q);
      setQaResult(res);
    } catch (err: any) {
      setError(err?.message || 'Q&A failed');
    }
  }

  return (
    <div className="container">
      <header className="app-header">
        <h1>DOCSENSE</h1>
        <p>Your AI Assistant for Rental & Loan Agreements</p>
      </header>

      <div className="disclaimer-banner">
        <p>AI-POWERED ANALYSIS — NOT A SUBSTITUTE FOR PROFESSIONAL LEGAL ADVICE.</p>
      </div>

      <div className="card upload-card">
        <input type="file" id="file-upload" accept=".pdf,.docx,.txt" onChange={onUpload} disabled={uploading} />
        <label htmlFor="file-upload" className="upload-button">
          {uploading ? 'Uploading...' : (objectName ? 'Choose Another File' : 'Choose File')}
        </label>
        {objectName && (
          <div className="file-status">
            <span className="file-name">File Added: {objectName.substring(0, 12)}...</span>
            {timeRemaining && <span className="timer">Auto-delete in: {timeRemaining}</span>}
          </div>
        )}
        {objectName && (
          <div className="actions-panel">
            <button onClick={onAnalyze} disabled={analyzing}>
              {analyzing ? 'Analyzing...' : 'Analyze Document'}
            </button>
            <button onClick={() => window.open(exportReportUrl(objectName, 'Rental'))} disabled={!objectName}>
              Export Report
            </button>
            <button onClick={onDelete} className="delete-button">Delete Now</button>
          </div>
        )}
      </div>

      {error && <div className="error-banner">{error}</div>}

      {overallScore && (
        <div className="card score-card" style={{ borderColor: overallScore.color }}>
          <h2>Overall Document Safety Score</h2>
          <div className="score-display">
            <span className="score-value" style={{ color: overallScore.color }}>{overallScore.value}/100</span>
            <span className="score-level" style={{ backgroundColor: overallScore.color }}>{overallScore.level}</span>
          </div>
        </div>
      )}

      {!!flags.length && (
        <div className="results-section">
          <h2>Analysis Results</h2>
          {flags.map((f) => (
            <div key={f.clause_id} className="card analysis-card">
              <div className="card-header">
                <span className={`severity-tag severity-${f.severity.toLowerCase()}`}>{f.severity}</span>
              </div>
              <p><strong>Justification:</strong> {f.reason}</p>
              {f.negotiation_hint && <p className="negotiation-hint"><strong>Negotiation Hint:</strong> {f.negotiation_hint}</p>}
              <details>
                <summary>Show Original Clause</summary>
                <p className="evidence-text">{f.evidence}</p>
              </details>
            </div>
          ))}
        </div>
      )}
      
      <div className="card qa-card">
        <h2>Ask a Question</h2>
        <div className="qa-input">
          <input 
            value={q} 
            onChange={e => setQ(e.target.value)} 
            placeholder="e.g., What is the notice period for termination?" 
          />
          <button onClick={onAsk} disabled={!objectName || !q}>Ask</button>
        </div>
        {qaResult && (
          <div className="qa-result">
            <p><strong>Answer:</strong> {qaResult.answer}</p>
            {qaResult.source_clause && (
              <details>
                <summary>Show Source Evidence</summary>
                <p className="evidence-text">{qaResult.source_clause.text}</p>
              </details>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App
