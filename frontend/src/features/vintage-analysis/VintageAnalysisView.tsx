import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { Calendar, HelpCircle, AlertCircle, Info } from 'lucide-react';

interface VintageAnalysisViewProps {
  reportingDate: string;
}

export const VintageAnalysisView: React.FC<VintageAnalysisViewProps> = ({ reportingDate }) => {
  const [vintageData, setVintageData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getVintageAnalysis(reportingDate)
      .then(res => {
        setVintageData(res);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [reportingDate]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Vintage & Cohort Analysis</h1>
          <p className="page-description">
            Track cumulative default rates across origination cohorts at fixed loan age milestones (1, 3, 6, 9, 12, 18, 24 months).
          </p>
        </div>
      </div>

      {/* PRD Compliance Banner */}
      <div className="explanation-panel" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
          <Info size={16} color="var(--accent-bronze)" />
          <span>
            <strong>Traceability Rule:</strong> In accordance with CredVista PRD standards, cohorts that have not yet reached a loan age milestone are explicitly marked as <em>Immature / Not Observable</em>. They are never conflated with zero defaults.
          </span>
        </div>
      </div>

      {/* Vintage Matrix Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Cumulative Default Rate (%) by Cohort and Loan Age</h2>
            <div className="card-subtitle">
              Reporting cutoff date: {vintageData?.reporting_date} | Observation intervals: months elapsed since origination
            </div>
          </div>
        </div>

        <div className="table-container">
          <table className="vintage-table">
            <thead>
              <tr>
                <th scope="col" style={{ textAlign: 'left' }}>Origination Cohort</th>
                <th scope="col">Loans</th>
                <th scope="col">Originated ($)</th>
                {vintageData?.loan_age_milestones?.map((m: number) => (
                  <th key={m} scope="col">Month {m}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', padding: '32px' }}>
                    Loading vintage matrix...
                  </td>
                </tr>
              ) : vintageData?.cohorts?.map((cohort: any) => (
                <tr key={cohort.origination_cohort}>
                  <td style={{ textAlign: 'left', fontWeight: 600 }}>
                    {cohort.origination_cohort}
                  </td>
                  <td>{cohort.cohort_loans_count}</td>
                  <td>${cohort.cohort_original_principal.toLocaleString()}</td>
                  {cohort.cells.map((cell: any, idx: number) => {
                    if (cell.is_immature) {
                      return (
                        <td key={idx} className="vintage-immature" title="Cohort has not reached this loan age yet">
                          Immature
                        </td>
                      );
                    }

                    const rate = cell.cumulative_default_rate ?? 0;
                    let cellClass = 'vintage-cell-good';
                    if (rate > 5.0) cellClass = 'vintage-cell-bad';
                    else if (rate > 2.0) cellClass = 'vintage-cell-warn';

                    return (
                      <td key={idx} className={cellClass} title={`${cohort.origination_cohort} at M${cell.loan_age_months}: ${rate}% cumulative default rate`}>
                        {rate.toFixed(1)}%
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', padding: '16px 20px', borderTop: '1px solid var(--border-color)', fontSize: '12px' }}>
          <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Color Scale:</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '12px', background: '#EEF8F1', border: '1px solid #BFE3CD', borderRadius: '2px' }} />
            <span>Low Default (0.0% – 2.0%)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '12px', background: '#FEF7EC', border: '1px solid #F7DCB0', borderRadius: '2px' }} />
            <span>Moderate Default (2.1% – 5.0%)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '12px', background: '#FCEBE9', border: '1px solid #F5C0BD', borderRadius: '2px' }} />
            <span>High Default (&gt; 5.0%)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '12px', background: '#F8F7F4', border: '1px solid #E6E1D8', borderRadius: '2px' }} />
            <span>Immature (Not Yet Observable)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
