import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { Download, FileText, CheckCircle, Clock, Plus, Filter } from 'lucide-react';

interface ReportsViewProps {
  reportingDate: string;
}

export const ReportsView: React.FC<ReportsViewProps> = ({ reportingDate }) => {
  const [history, setHistory] = useState<any[]>([]);
  const [generating, setGenerating] = useState(false);
  const [generatedReport, setGeneratedReport] = useState<any>(null);

  // Form state
  const [notes, setNotes] = useState('Monthly Credit Risk Committee Review');
  const [selectedRiskBands, setSelectedRiskBands] = useState<string[]>(['Low', 'Medium', 'High', 'Review Required']);
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>(['Active', 'Overdue', 'Delinquent', 'Defaulted']);

  const loadHistory = () => {
    api.getReportsHistory()
      .then(res => setHistory(res || []))
      .catch(console.error);
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleGenerate = (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    api.generateReport({
      user_id: 'risk_officer@credvista.internal',
      period_end: reportingDate,
      risk_bands: selectedRiskBands,
      loan_statuses: selectedStatuses,
      notes,
    }).then(res => {
      setGeneratedReport(res);
      setGenerating(false);
      loadHistory();
    }).catch(err => {
      console.error(err);
      setGenerating(false);
    });
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Portfolio Reports & Audit Exports</h1>
          <p className="page-description">
            Generate reproducible, versioned risk snapshots and download clean tabular CSV datasets with full metadata.
          </p>
        </div>
        <div>
          <a
            href={`/api/v1/reports/export.csv?reporting_date=${reportingDate}`}
            download
            className="btn btn-primary"
            style={{ textDecoration: 'none' }}
          >
            <Download size={15} /> Export Portfolio Data (.CSV)
          </a>
        </div>
      </div>

      {/* Generated Report Highlight Banner */}
      {generatedReport && (
        <div className="card" style={{ marginBottom: '24px', borderLeft: '4px solid var(--status-green)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle size={18} color="var(--status-green)" />
                <h3 style={{ fontSize: '16px' }}>Report Run Generated Successfully: {generatedReport.report_id}</h3>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Scope: {generatedReport.matching_loans_count} loans | Period ending: {generatedReport.period_end} | Metric Version: {generatedReport.metric_version}
              </p>
            </div>
            <a
              href={`/api/v1/reports/export.csv?reporting_date=${reportingDate}`}
              download
              className="btn btn-secondary"
            >
              <Download size={14} /> Download CSV
            </a>
          </div>
        </div>
      )}

      {/* Generator Form */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div>
            <h2 className="card-title">Generate Versioned Portfolio Snapshot</h2>
            <div className="card-subtitle">
              Saves an immutable snapshot into the database audit log with filter traceability
            </div>
          </div>
        </div>

        <form onSubmit={handleGenerate}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '16px' }}>
            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                Report Notes / Memo Title:
              </label>
              <input
                type="text"
                value={notes}
                onChange={e => setNotes(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-color)',
                  background: 'var(--surface-subtle)',
                }}
              />
            </div>

            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                Reporting Cutoff Date:
              </label>
              <input
                type="date"
                value={reportingDate}
                readOnly
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-color)',
                  background: 'var(--surface-subtle)',
                }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
            <button type="submit" className="btn btn-primary" disabled={generating}>
              <Plus size={15} /> {generating ? 'Generating Snapshot...' : 'Create Audited Report'}
            </button>
          </div>
        </form>
      </div>

      {/* Report History Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Report Run History & Audit Trail</h2>
            <div className="card-subtitle">Previous executive submissions and snapshot runs</div>
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th scope="col">Report ID</th>
                <th scope="col">Generated At</th>
                <th scope="col">Created By</th>
                <th scope="col">Period Cutoff</th>
                <th scope="col">Metric Version</th>
                <th scope="col">Outstanding Principal</th>
                <th scope="col">Default Rate</th>
                <th scope="col">Action</th>
              </tr>
            </thead>
            <tbody>
              {history.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                    No prior reports generated. Click 'Create Audited Report' above to generate the first snapshot.
                  </td>
                </tr>
              ) : history.map((r: any) => (
                <tr key={r.report_id}>
                  <td style={{ fontWeight: 600 }}>{r.report_id}</td>
                  <td>{new Date(r.generated_at).toLocaleString()}</td>
                  <td>{r.user_id}</td>
                  <td>{r.period_end}</td>
                  <td>{r.metric_version}</td>
                  <td style={{ fontWeight: 600 }}>
                    {r.portfolio_summary?.outstanding_principal?.formatted_value || '—'}
                  </td>
                  <td>{r.portfolio_summary?.default_rate?.formatted_value || '—'}</td>
                  <td>
                    <a
                      href={`/api/v1/reports/export.csv?reporting_date=${r.period_end || reportingDate}`}
                      download
                      className="btn btn-outline"
                      style={{ padding: '3px 8px', fontSize: '11px', textDecoration: 'none' }}
                    >
                      <Download size={12} /> CSV
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
