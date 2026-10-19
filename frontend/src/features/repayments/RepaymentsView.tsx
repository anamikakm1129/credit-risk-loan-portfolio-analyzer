import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { StatusBadge } from '../../components/StatusBadge';
import { ChevronLeft, ChevronRight, CheckCircle2, AlertTriangle, Clock, RefreshCw } from 'lucide-react';

interface RepaymentsViewProps {
  reportingDate: string;
  onSelectLoan: (id: string) => void;
}

export const RepaymentsView: React.FC<RepaymentsViewProps> = ({
  reportingDate,
  onSelectLoan,
}) => {
  const [overview, setOverview] = useState<any>(null);
  const [txItems, setTxItems] = useState<any[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [totalTx, setTotalTx] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.getRepaymentsOverview(reportingDate),
      api.getRepaymentTransactions({ page, page_size: pageSize }),
    ]).then(([ovRes, txRes]) => {
      setOverview(ovRes);
      setTxItems(txRes.items || []);
      setTotalTx(txRes.total || 0);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, [page, reportingDate]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Repayment & Delinquency Analysis</h1>
          <p className="page-description">
            Installment performance, delinquency aging buckets (DPD), and transaction reconciliation as of {reportingDate}.
          </p>
        </div>
      </div>

      {/* Top Repayment Summary Cards */}
      {overview && (
        <div className="kpi-grid" style={{ marginBottom: '24px' }}>
          <div className="card">
            <div className="kpi-label">Total Scheduled Due</div>
            <div className="kpi-value">${overview.total_due.toLocaleString()}</div>
            <div className="kpi-meta">Cumulative due to cutoff</div>
          </div>

          <div className="card">
            <div className="kpi-label">Total Collected</div>
            <div className="kpi-value" style={{ color: 'var(--status-green)' }}>
              ${overview.total_paid.toLocaleString()}
            </div>
            <div className="kpi-meta">Completed repayments</div>
          </div>

          <div className="card">
            <div className="kpi-label">Total Past Due</div>
            <div className="kpi-value" style={{ color: overview.total_overdue > 0 ? 'var(--status-red)' : 'inherit' }}>
              ${overview.total_overdue.toLocaleString()}
            </div>
            <div className="kpi-meta">Unpaid scheduled amounts</div>
          </div>

          <div className="card">
            <div className="kpi-label">Portfolio Repayment Rate</div>
            <div className="kpi-value">{overview.repayment_rate}%</div>
            <div className="kpi-meta">Collected vs scheduled due</div>
          </div>
        </div>
      )}

      {/* Aging Delinquency Buckets */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div>
            <h2 className="card-title">Delinquency Aging Buckets (Days Past Due)</h2>
            <div className="card-subtitle">
              Policy allocates payments using FIFO to earliest unpaid installment
            </div>
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th scope="col">Aging Bracket</th>
                <th scope="col">Loans Count</th>
                <th scope="col">Outstanding Principal ($)</th>
                <th scope="col">Overdue Amount ($)</th>
                <th scope="col">Portfolio Share (%)</th>
              </tr>
            </thead>
            <tbody>
              {overview?.aging_buckets?.map((bucket: any, idx: number) => {
                let badgeClass = 'badge-low';
                if (bucket.bucket_name.includes('Late')) badgeClass = 'badge-medium';
                if (bucket.bucket_name.includes('Delinquent') || bucket.bucket_name.includes('Defaulted')) badgeClass = 'badge-high';

                return (
                  <tr key={idx}>
                    <td>
                      <span className={`badge ${badgeClass}`} style={{ fontWeight: 600 }}>
                        {bucket.bucket_name}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600 }}>{bucket.loans_count}</td>
                    <td>${bucket.outstanding_principal.toLocaleString()}</td>
                    <td style={{ color: bucket.overdue_amount > 0 ? 'var(--status-red)' : 'inherit', fontWeight: 600 }}>
                      ${bucket.overdue_amount.toLocaleString()}
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ width: '80px', background: 'var(--surface-subtle)', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                          <div style={{ width: `${bucket.portfolio_share_pct}%`, height: '100%', background: 'var(--accent-bronze)' }} />
                        </div>
                        <span style={{ fontSize: '12px' }}>{bucket.portfolio_share_pct}%</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Recent Repayment Transactions</h2>
            <div className="card-subtitle">Audit of remittances, ACH transfers, and partial settlements</div>
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th scope="col">Payment ID</th>
                <th scope="col">Loan ID</th>
                <th scope="col">Borrower Name</th>
                <th scope="col">Payment Date</th>
                <th scope="col">Amount ($)</th>
                <th scope="col">Status</th>
                <th scope="col">Reference</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '32px' }}>
                    <div className="skeleton" style={{ height: '24px', width: '200px', margin: '0 auto 8px' }} />
                    <div style={{ color: 'var(--text-muted)' }}>Loading transactions...</div>
                  </td>
                </tr>
              ) : txItems.map((tx: any) => (
                <tr key={tx.payment_id}>
                  <td style={{ fontWeight: 600 }}>{tx.payment_id}</td>
                  <td>
                    <span
                      style={{ color: 'var(--accent-bronze)', cursor: 'pointer', fontWeight: 500 }}
                      onClick={() => onSelectLoan(tx.loan_id)}
                      title="Inspect loan details"
                    >
                      {tx.loan_id}
                    </span>
                  </td>
                  <td>{tx.borrower_name}</td>
                  <td>{tx.payment_date}</td>
                  <td style={{ fontWeight: 600, color: 'var(--status-green)' }}>
                    ${tx.amount.toFixed(2)}
                  </td>
                  <td>
                    <StatusBadge status={tx.payment_status} type="repayment" />
                  </td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{tx.reference || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px', fontSize: '13px', color: 'var(--text-secondary)' }}>
          <div>
            Showing {txItems.length > 0 ? (page - 1) * pageSize + 1 : 0} to{' '}
            {Math.min(page * pageSize, totalTx)} of {totalTx} transactions
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <button
              className="btn btn-secondary"
              style={{ padding: '4px 8px' }}
              disabled={page <= 1}
              onClick={() => setPage(p => Math.max(1, p - 1))}
            >
              <ChevronLeft size={16} /> Previous
            </button>
            <span>Page {page}</span>
            <button
              className="btn btn-secondary"
              style={{ padding: '4px 8px' }}
              disabled={page * pageSize >= totalTx}
              onClick={() => setPage(p => p + 1)}
            >
              Next <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

