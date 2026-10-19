import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { StatusBadge } from '../../components/StatusBadge';
import { Search, RotateCcw, ChevronLeft, ChevronRight, FileSpreadsheet } from 'lucide-react';

interface LoansViewProps {
  reportingDate: string;
  onSelectLoan: (id: string) => void;
  onSelectBorrower: (id: string) => void;
}

export const LoansView: React.FC<LoansViewProps> = ({
  reportingDate,
  onSelectLoan,
  onSelectBorrower,
}) => {
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('All');
  const [termMonths, setTermMonths] = useState<string>('');
  const [riskBand, setRiskBand] = useState('All');
  const [sortBy, setSortBy] = useState('issue_date');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const fetchLoans = () => {
    setLoading(true);
    api.getLoans({
      search,
      status: status !== 'All' ? status : undefined,
      term_months: termMonths ? Number(termMonths) : undefined,
      risk_band: riskBand !== 'All' ? riskBand : undefined,
      page,
      page_size: pageSize,
      sort_by: sortBy,
      sort_dir: sortDir,
      reporting_date: reportingDate,
    }).then(res => {
      setItems(res.items || []);
      setTotal(res.total || 0);
      setTotalPages(res.total_pages || 1);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  };

  useEffect(() => {
    fetchLoans();
  }, [page, sortBy, sortDir, status, riskBand, termMonths, reportingDate]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchLoans();
  };

  const handleReset = () => {
    setSearch('');
    setStatus('All');
    setTermMonths('');
    setRiskBand('All');
    setSortBy('issue_date');
    setSortDir('desc');
    setPage(1);
  };

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortDir('desc');
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Loan Directory</h1>
          <p className="page-description">
            Operational facility review, principal balances, repayment terms, and delinquency stages.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <form onSubmit={handleSearchSubmit} className="filter-bar">
        <div className="filter-group" style={{ flex: 1, minWidth: '220px' }}>
          <Search size={15} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search loan ID, borrower ID, or name..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ width: '100%' }}
          />
        </div>

        <div className="filter-group">
          <label htmlFor="filter-status">Status:</label>
          <select id="filter-status" value={status} onChange={e => { setStatus(e.target.value); setPage(1); }}>
            <option value="All">All Statuses</option>
            <option value="Active">Active</option>
            <option value="Overdue">Overdue</option>
            <option value="Delinquent">Delinquent</option>
            <option value="Defaulted">Defaulted</option>
            <option value="Settled">Settled</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="filter-term">Term:</label>
          <select id="filter-term" value={termMonths} onChange={e => { setTermMonths(e.target.value); setPage(1); }}>
            <option value="">All Terms</option>
            <option value="12">12 Months</option>
            <option value="24">24 Months</option>
            <option value="36">36 Months</option>
            <option value="48">48 Months</option>
            <option value="60">60 Months</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="filter-risk-band">Risk Band:</label>
          <select id="filter-risk-band" value={riskBand} onChange={e => { setRiskBand(e.target.value); setPage(1); }}>
            <option value="All">All Bands</option>
            <option value="Low">Low Risk</option>
            <option value="Medium">Medium Risk</option>
            <option value="High">High Risk</option>
            <option value="Review Required">Review Required</option>
          </select>
        </div>

        <button type="submit" className="btn btn-primary" style={{ padding: '6px 12px' }}>
          Apply
        </button>

        <button type="button" className="btn btn-outline" style={{ padding: '6px 12px' }} onClick={handleReset} title="Reset filters">
          <RotateCcw size={14} /> Reset
        </button>
      </form>

      {/* Loans Table */}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th scope="col" className="sortable" onClick={() => handleSort('loan_id')}>
                Loan ID {sortBy === 'loan_id' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th scope="col">Borrower</th>
              <th scope="col" className="sortable" onClick={() => handleSort('principal_amount')}>
                Principal {sortBy === 'principal_amount' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th scope="col" className="sortable" onClick={() => handleSort('issue_date')}>
                Issue Date {sortBy === 'issue_date' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th scope="col">Term / Rate</th>
              <th scope="col" className="sortable" onClick={() => handleSort('outstanding_principal')}>
                Outstanding {sortBy === 'outstanding_principal' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th scope="col" className="sortable" onClick={() => handleSort('overdue_amount')}>
                Overdue {sortBy === 'overdue_amount' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th scope="col" className="sortable" onClick={() => handleSort('days_past_due')}>
                DPD {sortBy === 'days_past_due' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th scope="col">Status</th>
              <th scope="col">Risk</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={10} style={{ textAlign: 'center', padding: '32px' }}>
                  <div className="skeleton" style={{ height: '24px', width: '200px', margin: '0 auto 8px' }} />
                  <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Loading loans...</div>
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={10} style={{ textAlign: 'center', padding: '48px', color: 'var(--text-secondary)' }}>
                  No loans found matching current filter criteria.
                </td>
              </tr>
            ) : (
              items.map((l: any) => (
                <tr key={l.loan_id} style={{ cursor: 'pointer' }} onClick={() => onSelectLoan(l.loan_id)}>
                  <td style={{ fontWeight: 600 }}>{l.loan_id}</td>
                  <td>
                    <span
                      style={{ color: 'var(--accent-bronze)', fontWeight: 500 }}
                      onClick={e => {
                        e.stopPropagation();
                        onSelectBorrower(l.borrower_id);
                      }}
                      title="View borrower profile"
                    >
                      {l.borrower_name}
                    </span>
                  </td>
                  <td style={{ fontWeight: 600 }}>${l.principal_amount.toLocaleString()}</td>
                  <td>{l.issue_date}</td>
                  <td>
                    {l.term_months}m @ {(l.annual_rate * 100).toFixed(1)}%
                  </td>
                  <td style={{ fontWeight: 600 }}>${l.outstanding_principal.toLocaleString()}</td>
                  <td style={{ color: l.overdue_amount > 0 ? 'var(--status-red)' : 'inherit', fontWeight: 600 }}>
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
                  <td>
                    <StatusBadge status={l.risk_band} type="risk" />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px', fontSize: '13px', color: 'var(--text-secondary)' }}>
        <div>
          Showing {items.length > 0 ? (page - 1) * pageSize + 1 : 0} to{' '}
          {Math.min(page * pageSize, total)} of {total} loans
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
          <span>
            Page {page} of {totalPages}
          </span>
          <button
            className="btn btn-secondary"
            style={{ padding: '4px 8px' }}
            disabled={page >= totalPages}
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
          >
            Next <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};
