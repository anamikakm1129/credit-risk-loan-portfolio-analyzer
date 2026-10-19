import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { StatusBadge } from '../../components/StatusBadge';
import { Search, RotateCcw, ChevronLeft, ChevronRight, UploadCloud } from 'lucide-react';

interface BorrowersViewProps {
  reportingDate: string;
  onSelectBorrower: (id: string) => void;
  initialSearch?: string;
  onNavigate?: (tab: string) => void;
}

export const BorrowersView: React.FC<BorrowersViewProps> = ({
  reportingDate,
  onSelectBorrower,
  initialSearch = '',
  onNavigate,
}) => {
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState(initialSearch);
  const [riskBand, setRiskBand] = useState('All');
  const [minScore, setMinScore] = useState<string>('');
  const [maxScore, setMaxScore] = useState<string>('');
  const [sortBy, setSortBy] = useState('borrower_id');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  const fetchBorrowers = () => {
    setLoading(true);
    api.getBorrowers({
      search,
      risk_band: riskBand !== 'All' ? riskBand : undefined,
      min_score: minScore ? Number(minScore) : undefined,
      max_score: maxScore ? Number(maxScore) : undefined,
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
    fetchBorrowers();
  }, [page, sortBy, sortDir, riskBand, reportingDate]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchBorrowers();
  };

  const handleReset = () => {
    setSearch('');
    setRiskBand('All');
    setMinScore('');
    setMaxScore('');
    setSortBy('borrower_id');
    setSortDir('asc');
    setPage(1);
  };

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortDir('asc');
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Borrower Directory</h1>
          <p className="page-description">
            Search, filter, and inspect borrower profiles, DTI ratios, and versioned risk classifications.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <form onSubmit={handleSearchSubmit} className="filter-bar">
        <div className="filter-group" style={{ flex: 1, minWidth: '240px' }}>
          <Search size={18} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search borrower by name or ID..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ width: '100%' }}
          />
        </div>

        <div className="filter-group">
          <label htmlFor="filter-risk">Risk Band:</label>
          <select id="filter-risk" value={riskBand} onChange={e => { setRiskBand(e.target.value); setPage(1); }}>
            <option value="All">All Risk Bands</option>
            <option value="Low">Low Risk</option>
            <option value="Medium">Medium Risk</option>
            <option value="High">High Risk</option>
            <option value="Review Required">Review Required</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="filter-score">Score Min:</label>
          <input
            id="filter-score"
            type="number"
            placeholder="300"
            style={{ width: '90px' }}
            value={minScore}
            onChange={e => setMinScore(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label htmlFor="filter-score-max">Max:</label>
          <input
            id="filter-score-max"
            type="number"
            placeholder="850"
            style={{ width: '90px' }}
            value={maxScore}
            onChange={e => setMaxScore(e.target.value)}
          />
        </div>

        <button type="submit" className="btn btn-primary">
          Apply
        </button>

        <button type="button" className="btn btn-outline" onClick={handleReset} title="Reset all filters">
          <RotateCcw size={16} /> Reset
        </button>
      </form>

      {/* Table Container */}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th scope="col" className="sortable" onClick={() => handleSort('borrower_id')}>
                Borrower ID {sortBy === 'borrower_id' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th scope="col" className="sortable" onClick={() => handleSort('full_name')}>
                Full Name {sortBy === 'full_name' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th scope="col" className="sortable" onClick={() => handleSort('credit_score')}>
                Credit Score {sortBy === 'credit_score' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th scope="col" className="sortable" onClick={() => handleSort('annual_income')}>
                Annual Income {sortBy === 'annual_income' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th scope="col" className="sortable" onClick={() => handleSort('dti')}>
                DTI Ratio {sortBy === 'dti' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th scope="col" className="sortable" onClick={() => handleSort('exposure')}>
                Active Exposure {sortBy === 'exposure' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th scope="col" className="sortable" onClick={() => handleSort('overdue')}>
                Overdue {sortBy === 'overdue' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th scope="col">Risk Band</th>
              <th scope="col">Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '40px' }}>
                  <div className="skeleton" style={{ height: '28px', width: '220px', margin: '0 auto 10px' }} />
                  <div style={{ color: 'var(--text-muted)', fontSize: '15px' }}>Loading borrowers...</div>
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '56px', color: 'var(--text-secondary)' }}>
                  <div style={{ fontSize: '18px', fontWeight: 600, marginBottom: '8px' }}>
                    No borrowers found in database
                  </div>
                  <p style={{ fontSize: '15px', color: 'var(--text-muted)', marginBottom: '18px' }}>
                    Upload your borrowers CSV file via the Data Quality portal to populate this directory.
                  </p>
                </td>
              </tr>
            ) : (
              items.map((b: any) => (
                <tr key={b.borrower_id} style={{ cursor: 'pointer' }} onClick={() => onSelectBorrower(b.borrower_id)}>
                  <td style={{ fontWeight: 700 }}>{b.borrower_id}</td>
                  <td>{b.full_name}</td>
                  <td>
                    {b.credit_score ?? (
                      <span style={{ color: 'var(--status-red)', fontWeight: 700 }}>
                        Missing
                      </span>
                    )}
                  </td>
                  <td>{b.annual_income ? `$${b.annual_income.toLocaleString()}` : '—'}</td>
                  <td>{b.dti_ratio !== null ? `${b.dti_ratio}%` : '—'}</td>
                  <td style={{ fontWeight: 700 }}>${b.total_exposure.toLocaleString()}</td>
                  <td style={{ color: b.total_overdue > 0 ? 'var(--status-red)' : 'inherit', fontWeight: 700 }}>
                    ${b.total_overdue.toLocaleString()}
                  </td>
                  <td>
                    <StatusBadge status={b.risk_band} type="risk" />
                  </td>
                  <td>
                    <button
                      className="btn btn-outline"
                      style={{ padding: '4px 10px', fontSize: '13px' }}
                      onClick={e => {
                        e.stopPropagation();
                        onSelectBorrower(b.borrower_id);
                      }}
                    >
                      Profile
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {total > 0 && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '20px', fontSize: '14.5px', color: 'var(--text-secondary)' }}>
          <div>
            Showing {(page - 1) * pageSize + 1} to{' '}
            {Math.min(page * pageSize, total)} of {total} borrowers
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <button
              className="btn btn-secondary"
              style={{ padding: '6px 12px' }}
              disabled={page <= 1}
              onClick={() => setPage(p => Math.max(1, p - 1))}
            >
              <ChevronLeft size={18} /> Previous
            </button>
            <span style={{ fontWeight: 600 }}>
              Page {page} of {totalPages}
            </span>
            <button
              className="btn btn-secondary"
              style={{ padding: '6px 12px' }}
              disabled={page >= totalPages}
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            >
              Next <ChevronRight size={18} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
