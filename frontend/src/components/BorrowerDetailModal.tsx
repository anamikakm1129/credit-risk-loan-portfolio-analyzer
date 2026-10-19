import React, { useEffect, useState } from 'react';
import { X, ShieldAlert, CheckCircle, AlertTriangle, FileText, Calendar, DollarSign, CreditCard } from 'lucide-react';
import { api } from '../services/api';
import { StatusBadge } from './StatusBadge';

interface BorrowerDetailModalProps {
  borrowerId: string | null;
  onClose: () => void;
  reportingDate: string;
}

export const BorrowerDetailModal: React.FC<BorrowerDetailModalProps> = ({
  borrowerId,
  onClose,
  reportingDate,
}) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!borrowerId) return;
    setLoading(true);
    api.getBorrowerProfile(borrowerId, reportingDate)
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [borrowerId, reportingDate]);

  if (!borrowerId) return null;

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="modal-borrower-title">
      <div className="modal-content">
        <div className="modal-header">
          <div>
            <h2 id="modal-borrower-title" className="card-title" style={{ fontSize: '20px' }}>
              Borrower Profile: {borrowerId}
            </h2>
            <div className="card-subtitle">{data?.full_name || 'Loading details...'}</div>
          </div>
          <button className="btn btn-outline" onClick={onClose} aria-label="Close profile modal">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          {loading && (
            <div className="empty-state">
              <div className="skeleton" style={{ height: '40px', marginBottom: '16px' }} />
              <div className="skeleton" style={{ height: '120px', marginBottom: '16px' }} />
              <div className="skeleton" style={{ height: '200px' }} />
            </div>
          )}

          {error && (
            <div className="explanation-panel high-risk">
              <strong>Failed to load borrower profile:</strong> {error}
            </div>
          )}

          {data && (
            <>
              {/* Financial Snapshot */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' }}>
                <div style={{ background: 'var(--surface-subtle)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Credit Score</div>
                  <div style={{ fontSize: '18px', fontWeight: 700, marginTop: '4px' }}>
                    {data.credit_score ?? <span style={{ color: 'var(--status-red)', fontSize: '14px' }}>Missing</span>}
                  </div>
                </div>

                <div style={{ background: 'var(--surface-subtle)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Annual Income</div>
                  <div style={{ fontSize: '18px', fontWeight: 700, marginTop: '4px' }}>
                    {data.annual_income ? `$${data.annual_income.toLocaleString()}` : <span style={{ color: 'var(--status-red)', fontSize: '14px' }}>Missing</span>}
                  </div>
                </div>

                <div style={{ background: 'var(--surface-subtle)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>DTI Ratio</div>
                  <div style={{ fontSize: '18px', fontWeight: 700, marginTop: '4px' }}>
                    {data.dti_ratio !== null ? `${data.dti_ratio}%` : 'N/A'}
                  </div>
                </div>

                <div style={{ background: 'var(--surface-subtle)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Risk Band</div>
                  <div style={{ marginTop: '4px' }}>
                    <StatusBadge status={data.risk_band} type="risk" />
                  </div>
                </div>
              </div>

              {/* Explainable Risk Engine Assessment */}
              <div style={{ marginBottom: '24px' }}>
                <h3 style={{ fontSize: '15px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldAlert size={16} color="var(--accent-bronze)" />
                  Risk Engine Assessment (Ruleset {data.risk_assessment?.rule_version || 'v1.0'})
                </h3>

                <div className={`explanation-panel ${data.risk_band === 'High' ? 'high-risk' : (data.risk_band === 'Review Required' ? 'review-required' : '')}`}>
                  <p style={{ fontSize: '13.5px', marginBottom: '10px' }}>
                    {data.risk_assessment?.plain_language_explanation}
                  </p>

                  {data.risk_assessment?.factors?.reasons?.length > 0 && (
                    <div style={{ fontSize: '12.5px', marginTop: '6px' }}>
                      <strong>Contributing Factors:</strong>
                      <ul style={{ paddingLeft: '20px', marginTop: '4px' }}>
                        {data.risk_assessment.factors.reasons.map((r: string, idx: number) => (
                          <li key={idx} style={{ marginBottom: '2px' }}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {data.risk_assessment?.factors?.missing_inputs?.length > 0 && (
                    <div style={{ fontSize: '12.5px', marginTop: '8px', color: 'var(--status-red)' }}>
                      <strong>Missing Inputs Warning:</strong> {data.risk_assessment.factors.missing_inputs.join(', ')}
                    </div>
                  )}
                </div>
              </div>

              {/* Loans List */}
              <div style={{ marginBottom: '20px' }}>
                <h3 style={{ fontSize: '15px', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <CreditCard size={16} color="var(--accent-bronze)" />
                  Associated Loans ({data.loans?.length || 0})
                </h3>

                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th scope="col">Loan ID</th>
                        <th scope="col">Principal</th>
                        <th scope="col">Issue Date</th>
                        <th scope="col">Term</th>
                        <th scope="col">Outstanding</th>
                        <th scope="col">Overdue</th>
                        <th scope="col">DPD</th>
                        <th scope="col">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.loans?.map((l: any) => (
                        <tr key={l.loan_id}>
                          <td style={{ fontWeight: 600 }}>{l.loan_id}</td>
                          <td>${l.principal_amount.toLocaleString()}</td>
                          <td>{l.issue_date}</td>
                          <td>{l.term_months}m</td>
                          <td style={{ fontWeight: 600 }}>${l.outstanding_principal.toLocaleString()}</td>
                          <td style={{ color: l.overdue_amount > 0 ? 'var(--status-red)' : 'inherit' }}>
                            ${l.overdue_amount.toLocaleString()}
                          </td>
                          <td>
                            {l.days_past_due > 0 ? (
                              <span style={{ color: 'var(--status-red)', fontWeight: 600 }}>{l.days_past_due}d</span>
                            ) : (
                              '0d'
                            )}
                          </td>
                          <td>
                            <StatusBadge status={l.status} type="loan" />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Repayments summary */}
              {data.repayment_summary && (
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '14px', background: 'var(--surface-subtle)', borderRadius: 'var(--radius-sm)', fontSize: '13px' }}>
                  <div>Total Due: <strong>${data.repayment_summary.total_due.toLocaleString()}</strong></div>
                  <div>Total Paid: <strong style={{ color: 'var(--status-green)' }}>${data.repayment_summary.total_paid.toLocaleString()}</strong></div>
                  <div>Total Overdue: <strong style={{ color: data.repayment_summary.total_overdue > 0 ? 'var(--status-red)' : 'inherit' }}>${data.repayment_summary.total_overdue.toLocaleString()}</strong></div>
                  <div>Repayment Rate: <strong>{data.repayment_summary.overall_repayment_rate}%</strong></div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
