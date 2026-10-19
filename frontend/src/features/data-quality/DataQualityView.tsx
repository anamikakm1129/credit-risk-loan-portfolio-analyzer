import React, { useEffect, useState } from 'react';
import { api, API_BASE } from '../../services/api';
import { StatusBadge } from '../../components/StatusBadge';
import { UploadCloud, Download, Play, CheckCircle2, Trash2, FileSpreadsheet, AlertCircle } from 'lucide-react';

export const DataQualityView: React.FC = () => {
  const [qualityData, setQualityData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  // File upload state
  const [borrowersFile, setBorrowersFile] = useState<File | null>(null);
  const [loansFile, setLoansFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const loadLatest = () => {
    setLoading(true);
    api.getLatestDataQuality()
      .then(res => {
        setQualityData(res);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadLatest();
  }, []);

  const handleRunDiagnostics = () => {
    setRunning(true);
    api.runDataQualityDiagnostics()
      .then(res => {
        setQualityData(res);
        setRunning(false);
      })
      .catch(err => {
        console.error(err);
        setRunning(false);
      });
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!borrowersFile && !loansFile) {
      alert('Please select at least a Borrowers CSV or Loans CSV file to upload.');
      return;
    }

    setUploading(true);
    setUploadResult(null);
    setUploadError(null);

    const formData = new FormData();
    if (borrowersFile) formData.append('borrowers_file', borrowersFile);
    if (loansFile) formData.append('loans_file', loansFile);

    try {
      const res = await fetch(`${API_BASE}/data-quality/upload`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`Upload failed: ${txt}`);
      }
      const data = await res.json();
      setUploadResult(data);
      setUploading(false);
      setBorrowersFile(null);
      setLoansFile(null);
      loadLatest();
    } catch (err: any) {
      setUploadError(err.message);
      setUploading(false);
    }
  };

  const handleClearData = async () => {
    if (!window.confirm('Are you sure you want to clear all portfolio data? This will remove all borrower and loan records.')) {
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/data-quality/clear-portfolio`, { method: 'POST' });
      if (res.ok) {
        alert('All portfolio records have been cleared.');
        setUploadResult(null);
        loadLatest();
      }
    } catch (err: any) {
      alert(`Error clearing data: ${err.message}`);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Portfolio Ingestion & Data Quality</h1>
          <p className="page-description">
            Upload your own borrower and loan CSV files, inspect validation health, and enforce zero-defect data standards.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn btn-outline" onClick={handleClearData} style={{ color: 'var(--status-red)' }} title="Clear all loaded data">
            <Trash2 size={16} /> Reset Database
          </button>
          <button className="btn btn-primary" onClick={handleRunDiagnostics} disabled={running}>
            <Play size={16} /> {running ? 'Running Diagnostic Audit...' : 'Run Diagnostics'}
          </button>
        </div>
      </div>

      {/* CSV Upload Portal */}
      <div className="card" style={{ marginBottom: '28px', border: '2px dashed var(--accent-bronze)' }}>
        <div className="card-header">
          <div>
            <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <UploadCloud size={24} color="var(--accent-bronze)" />
              Upload Your Portfolio Data (CSV)
            </h2>
            <div className="card-subtitle">
              Select your custom borrower and loan files. Data is automatically validated, audited, and ingested.
            </div>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <a
              href={`${API_BASE}/data-quality/templates/borrowers.csv`}
              download="borrowers_template.csv"
              className="btn btn-secondary"
              style={{ fontSize: '13.5px', padding: '6px 12px', textDecoration: 'none' }}
            >
              <Download size={14} /> Borrowers Template
            </a>
            <a
              href={`${API_BASE}/data-quality/templates/loans.csv`}
              download="loans_template.csv"
              className="btn btn-secondary"
              style={{ fontSize: '13.5px', padding: '6px 12px', textDecoration: 'none' }}
            >
              <Download size={14} /> Loans Template
            </a>
          </div>
        </div>

        <form onSubmit={handleUploadSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', margin: '16px 0 24px 0' }}>
            {/* Borrowers Upload Box */}
            <div style={{ background: 'var(--surface-subtle)', padding: '20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
              <label style={{ fontSize: '15px', fontWeight: 700, display: 'block', marginBottom: '8px' }}>
                1. Borrowers CSV File:
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={e => setBorrowersFile(e.target.files?.[0] || null)}
                style={{ fontSize: '14.5px', width: '100%' }}
              />
              <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '8px' }}>
                Columns: <code>borrower_id, full_name, annual_income, credit_score, monthly_debt_obligations, employment_status, home_ownership</code>
              </div>
            </div>

            {/* Loans Upload Box */}
            <div style={{ background: 'var(--surface-subtle)', padding: '20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
              <label style={{ fontSize: '15px', fontWeight: 700, display: 'block', marginBottom: '8px' }}>
                2. Loans CSV File:
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={e => setLoansFile(e.target.files?.[0] || null)}
                style={{ fontSize: '14.5px', width: '100%' }}
              />
              <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '8px' }}>
                Columns: <code>loan_id, borrower_id, principal_amount, issue_date, term_months, annual_rate, status, outstanding_principal, purpose</code>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button
              type="submit"
              className="btn btn-primary"
              style={{ padding: '10px 24px', fontSize: '15.5px' }}
              disabled={uploading || (!borrowersFile && !loansFile)}
            >
              <UploadCloud size={18} /> {uploading ? 'Processing & Ingesting...' : 'Upload & Ingest Portfolio'}
            </button>
          </div>
        </form>

        {/* Upload Success / Error Callout */}
        {uploadResult && (
          <div className="explanation-panel" style={{ marginTop: '20px', borderLeftColor: 'var(--status-green)', background: 'var(--status-green-bg)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '15px' }}>
              <CheckCircle2 size={20} color="var(--status-green)" />
              <div>
                <strong>Ingestion Complete!</strong> Successfully processed {uploadResult.records_read} records ({uploadResult.records_accepted} accepted, {uploadResult.records_rejected} rejected).
              </div>
            </div>
          </div>
        )}

        {uploadError && (
          <div className="explanation-panel high-risk" style={{ marginTop: '20px' }}>
            <strong>Upload Error:</strong> {uploadError}
          </div>
        )}
      </div>

      {/* Diagnostics Summary Cards */}
      {qualityData && (
        <div className="kpi-grid" style={{ marginBottom: '28px' }}>
          <div className="card">
            <div className="kpi-label">Health Status</div>
            <div className="kpi-value" style={{ fontSize: '24px' }}>
              <StatusBadge status={qualityData.status} type="risk" />
            </div>
            <div className="kpi-meta">Evaluated: {new Date(qualityData.evaluated_at).toLocaleTimeString()}</div>
          </div>

          <div className="card">
            <div className="kpi-label">Total Records Evaluated</div>
            <div className="kpi-value">{qualityData.total_records_checked}</div>
            <div className="kpi-meta">Borrower & facility entities</div>
          </div>

          <div className="card">
            <div className="kpi-label">Clean Verified Records</div>
            <div className="kpi-value" style={{ color: 'var(--status-green)' }}>
              {qualityData.clean_records_count ?? (qualityData.total_records_checked - (qualityData.issues?.length || 0))}
            </div>
            <div className="kpi-meta">Satisfied all validation rules</div>
          </div>

          <div className="card">
            <div className="kpi-label">Flagged Issues</div>
            <div className="kpi-value" style={{ color: qualityData.issues?.length > 0 ? 'var(--status-amber)' : 'inherit' }}>
              {qualityData.issues?.length || 0}
            </div>
            <div className="kpi-meta">Quarantined for analyst review</div>
          </div>
        </div>
      )}

      {/* Issue Details Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Diagnostic Findings ({qualityData?.issues?.length || 0} Items)</h2>
            <div className="card-subtitle">Detailed exceptions, duplicate IDs, missing inputs, and boundary warnings</div>
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th scope="col">Severity</th>
                <th scope="col">Issue Category</th>
                <th scope="col">Entity</th>
                <th scope="col">Record ID</th>
                <th scope="col">Field</th>
                <th scope="col">Diagnostic Detail</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '36px' }}>Running diagnostics...</td>
                </tr>
              ) : qualityData?.issues?.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '56px', color: 'var(--status-green)' }}>
                    <CheckCircle2 size={36} style={{ margin: '0 auto 10px' }} />
                    <div style={{ fontSize: '17px', fontWeight: 600 }}>
                      {qualityData.total_records_checked > 0 ? 'Zero data defects! All records pass validation.' : 'No data in portfolio. Upload your CSV files above to begin.'}
                    </div>
                  </td>
                </tr>
              ) : qualityData?.issues?.map((iss: any, idx: number) => (
                <tr key={idx}>
                  <td>
                    <span className={`badge ${iss.severity === 'Critical' ? 'badge-high' : 'badge-medium'}`}>
                      {iss.severity}
                    </span>
                  </td>
                  <td style={{ fontWeight: 700 }}>{iss.issue_type}</td>
                  <td>{iss.entity}</td>
                  <td style={{ fontWeight: 700 }}>{iss.record_id}</td>
                  <td><code>{iss.field}</code></td>
                  <td>{iss.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
