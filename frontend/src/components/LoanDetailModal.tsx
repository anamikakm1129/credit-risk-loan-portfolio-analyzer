import React, { useEffect, useState } from 'react';
import { X, Calendar, DollarSign, Clock, CheckCircle, AlertCircle, FileText } from 'lucide-react';
import { api } from '../services/api';
import { StatusBadge } from './StatusBadge';

interface LoanDetailModalProps {
  loanId: string | null;
  onClose: () => void;
  reportingDate: string;
}

export const LoanDetailModal: React.FC<LoanDetailModalProps> = ({
  loanId,
  onClose,
  reportingDate,
}) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loanId) return;
    setLoading(true);
    api.getLoanDetail(loanId, reportingDate)
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [loanId, reportingDate]);

  if (!loanId) return null;

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="modal-loan-title">
      <div className="modal-content" style={{ maxWidth: '820px' }}>
        <div className="modal-header">
          <div>
            <h2 id="modal-loan-title" className="card-title" style={{ fontSize: '20px' }}>
              Loan Details: {loanId}
            </h2>
            <div className="card-subtitle">
              Borrower: {data?.borrower?.full_name} ({data?.borrower?.borrower_id})
            </div>
          </div>
          <button className="btn btn-outline" onClick={onClose} aria-label="Close loan modal">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          {loading && (
            <div className="empty-state">
              <div className="skeleton" style={{ height: '50px', marginBottom: '16px' }} />
              <div className="skeleton" style={{ height: '140px' }} />
            </div>
          )}

          {error && (
            <div className="explanation-panel high-risk">
              <strong>Error loading loan details:</strong> {error}
            </div>
          )}

          {data && (
            <>
              {/* Headline Loan Stats */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' }}>
                <div style={{ background: 'var(--surface-subtle)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Principal Amount</div>
                  <div style={{ fontSize: '18px', fontWeight: 700, marginTop: '4px' }}>
                    ${data.principal_amount.toLocaleString()}
                  </div>
                </div>

                <div style={{ background: 'var(--surface-subtle)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Outstanding Balance</div>
                  <div style={{ fontSize: '18px', fontWeight: 700, marginTop: '4px' }}>
                    ${data.outstanding_principal.toLocaleString()}
                  </div>
                </div>

                <div style={{ background: 'var(--surface-subtle)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Interest Rate</div>
                  <div style={{ fontSize: '18px', fontWeight: 700, marginTop: '4px' }}>
                    {(data.annual_rate * 100).toFixed(2)}%
                  </div>
                </div>

                <div style={{ background: 'var(--surface-subtle)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Loan Status</div>
                  <div style={{ marginTop: '4px' }}>
                    <StatusBadge status={data.status} type="loan" />
                  </div>
                </div>
              </div>

              {/* Repayment Health Banner */}
              <div className={`explanation-panel ${data.repayment_state.overdue_amount > 0 ? 'high-risk' : ''}`} style={{ marginBottom: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <strong>Repayment Status: {data.repayment_state.delinquency_stage}</strong>
                    <div style={{ fontSize: '12.5px', marginTop: '4px' }}>
                      Overdue Amount: <strong>${data.repayment_state.overdue_amount.toLocaleString()}</strong> | 
                      Days Past Due: <strong>{data.repayment_state.days_past_due} days</strong>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right', fontSize: '12.5px' }}>
                    Repayment Collection Rate: <strong>{data.repayment_state.repayment_rate}%</strong>
                  </div>
                </div>
              </div>

              {/* Repayment Schedule */}
              <div style={{ marginBottom: '20px' }}>
                <h3 style={{ fontSize: '15px', marginBottom: '10px' }}>
                  Repayment Schedule ({data.schedules?.length || 0} Instalments)
                </h3>
                <div className="table-container" style={{ maxHeight: '240px', overflowY: 'auto' }}>
                  <table>
                    <thead>
                      <tr>
                        <th scope="col">#</th>
                        <th scope="col">Due Date</th>
                        <th scope="col">Scheduled ($)</th>
                        <th scope="col">Principal</th>
                        <th scope="col">Interest</th>
                        <th scope="col">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.schedules?.map((s: any) => (
                        <tr key={s.schedule_id}>
                          <td>{s.installment_number}</td>
                          <td>{s.due_date}</td>
                          <td style={{ fontWeight: 600 }}>${s.scheduled_amount.toFixed(2)}</td>
                          <td>${s.principal_due.toFixed(2)}</td>
                          <td>${s.interest_due.toFixed(2)}</td>
                          <td>
                            <StatusBadge status={s.status} type="repayment" />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Transactions History */}
              <div>
                <h3 style={{ fontSize: '15px', marginBottom: '10px' }}>
                  Recorded Transactions ({data.transactions?.length || 0})
                </h3>
                <div className="table-container" style={{ maxHeight: '200px', overflowY: 'auto' }}>
                  <table>
                    <thead>
                      <tr>
                        <th scope="col">Payment ID</th>
                        <th scope="col">Date</th>
                        <th scope="col">Amount ($)</th>
                        <th scope="col">Status</th>
                        <th scope="col">Reference</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.transactions?.map((t: any) => (
                        <tr key={t.payment_id}>
                          <td style={{ fontWeight: 600 }}>{t.payment_id}</td>
                          <td>{t.payment_date}</td>
                          <td style={{ fontWeight: 600, color: 'var(--status-green)' }}>
                            ${t.amount.toFixed(2)}
                          </td>
                          <td>
                            <StatusBadge status={t.payment_status} type="repayment" />
                          </td>
                          <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{t.reference || '—'}</td>
                        </tr>
                      ))}
                      {data.transactions?.length === 0 && (
                        <tr>
                          <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>
                            No payment transactions recorded for this loan.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
