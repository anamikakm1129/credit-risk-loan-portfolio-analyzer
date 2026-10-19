import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { StatusBadge } from '../../components/StatusBadge';
import { ShieldCheck, AlertTriangle, AlertCircle, Play, CheckCircle2, FileCheck } from 'lucide-react';

export const DataQualityView: React.FC = () => {
  const [qualityData, setQualityData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

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

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Data Quality & Ingestion Diagnostics</h1>
          <p className="page-description">
            Audit portfolio data integrity: detects missing critical inputs, invalid numbers, duplicate IDs, and orphan references.
          </p>
        </div>
        <div>
          <button className="btn btn-primary" onClick={handleRunDiagnostics} disabled={running}>
            <Play size={14} /> {running ? 'Running Full Diagnostic Audit...' : 'Run Diagnostics Now'}
          </button>
        </div>
      </div>

      {/* Diagnostics Summary Cards */}
      {qualityData && (
        <div className="kpi-grid" style={{ marginBottom: '24px' }}>
          <div className="card">
            <div className="kpi-label">Overall Health Status</div>
            <div className="kpi-value" style={{ fontSize: '22px' }}>
              <StatusBadge status={qualityData.status} type="risk" />
            </div>
            <div className="kpi-meta">Evaluated: {new Date(qualityData.evaluated_at).toLocaleTimeString()}</div>
          </div>

          <div className="card">
            <div className="kpi-label">Total Records Checked</div>
            <div className="kpi-value">{qualityData.total_records_checked}</div>
            <div className="kpi-meta">Borrower & Loan entities</div>
          </div>

          <div className="card">
            <div className="kpi-label">Clean Verified Records</div>
            <div className="kpi-value" style={{ color: 'var(--status-green)' }}>
              {qualityData.clean_records_count ?? (qualityData.total_records_checked - (qualityData.issues?.length || 0))}
            </div>
            <div className="kpi-meta">Passed all validation rules</div>
          </div>

          <div className="card">
            <div className="kpi-label">Flagged Issues</div>
            <div className="kpi-value" style={{ color: qualityData.issues?.length > 0 ? 'var(--status-amber)' : 'inherit' }}>
              {qualityData.issues?.length || 0}
            </div>
            <div className="kpi-meta">Review required triggers</div>
          </div>
        </div>
      )}

      {/* Policy Mandate Callout */}
      <div className="explanation-panel" style={{ marginBottom: '24px' }}>
        <strong>PRD Data Integrity Policy:</strong> Missing inputs (such as missing credit score or unverified income) are strictly quarantined as <em>Review Required</em> in risk segmentation. The system never silently assumes zero debt or prime credit scores.
      </div>

      {/* Issue Details Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Diagnostic Findings ({qualityData?.issues?.length || 0} Items)</h2>
            <div className="card-subtitle">Active data quality exceptions in the portfolio database</div>
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
                  <td colSpan={6} style={{ textAlign: 'center', padding: '32px' }}>Running diagnostics...</td>
                </tr>
              ) : qualityData?.issues?.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '48px', color: 'var(--status-green)' }}>
                    <CheckCircle2 size={32} style={{ margin: '0 auto 8px' }} />
                    <div>All borrower and loan records satisfy data quality rules!</div>
                  </td>
                </tr>
              ) : qualityData?.issues?.map((iss: any, idx: number) => (
                <tr key={idx}>
                  <td>
                    <span className={`badge ${iss.severity === 'Critical' ? 'badge-high' : 'badge-medium'}`}>
                      {iss.severity}
                    </span>
                  </td>
                  <td style={{ fontWeight: 600 }}>{iss.issue_type}</td>
                  <td>{iss.entity}</td>
                  <td style={{ fontWeight: 600 }}>{iss.record_id}</td>
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
