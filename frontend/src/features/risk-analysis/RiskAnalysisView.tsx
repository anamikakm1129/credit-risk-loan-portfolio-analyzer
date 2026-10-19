import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { StatusBadge } from '../../components/StatusBadge';
import { Sliders, ShieldAlert, CheckCircle, RotateCcw, Play } from 'lucide-react';

interface RiskAnalysisViewProps {
  reportingDate: string;
}

export const RiskAnalysisView: React.FC<RiskAnalysisViewProps> = ({ reportingDate }) => {
  const [segmentsData, setSegmentsData] = useState<any>(null);
  const [scoreBands, setScoreBands] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Simulation parameters
  const [highDtiPct, setHighDtiPct] = useState(43.0);
  const [lowScoreThreshold, setLowScoreThreshold] = useState(620);
  const [overdueDaysThreshold, setOverdueDaysThreshold] = useState(30);
  const [simResults, setSimResults] = useState<any>(null);
  const [simulating, setSimulating] = useState(false);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.getRiskSegments(reportingDate),
      api.getCreditScoreBands(reportingDate),
    ]).then(([segRes, bandRes]) => {
      setSegmentsData(segRes);
      setScoreBands(bandRes.bands || []);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, [reportingDate]);

  const runSimulation = () => {
    setSimulating(true);
    api.simulateRisk({
      high_dti_pct: Number(highDtiPct),
      low_score_threshold: Number(lowScoreThreshold),
      overdue_days_threshold: Number(overdueDaysThreshold),
      reporting_date: reportingDate,
    }).then(res => {
      setSimResults(res);
      setSimulating(false);
    }).catch(err => {
      console.error(err);
      setSimulating(false);
    });
  };

  const resetSimulation = () => {
    setHighDtiPct(43.0);
    setLowScoreThreshold(620);
    setOverdueDaysThreshold(30);
    setSimResults(null);
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Risk Segmentation & Policy Simulator</h1>
          <p className="page-description">
            Transparent, explainable risk rules (Ruleset {segmentsData?.rule_version || 'v1.0'}), credit score bands, and scenario stress-testing.
          </p>
        </div>
      </div>

      {/* Segments Distribution Table */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div>
            <h2 className="card-title">Active Portfolio Segmentation Distribution</h2>
            <div className="card-subtitle">
              Effective Date: {segmentsData?.rule_effective_date} | Total Portfolio Exposure: ${segmentsData?.total_exposure?.toLocaleString()}
            </div>
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th scope="col">Risk Band</th>
                <th scope="col">Borrowers</th>
                <th scope="col">Borrower Share (%)</th>
                <th scope="col">Total Exposure ($)</th>
                <th scope="col">Exposure Share (%)</th>
                <th scope="col">Avg DTI (%)</th>
                <th scope="col">Avg Score</th>
                <th scope="col">Overdue Amount ($)</th>
                <th scope="col">Default Rate (%)</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '32px' }}>Loading risk segments...</td>
                </tr>
              ) : segmentsData?.segments?.map((seg: any) => (
                <tr key={seg.risk_band}>
                  <td>
                    <StatusBadge status={seg.risk_band} type="risk" />
                  </td>
                  <td style={{ fontWeight: 600 }}>{seg.borrower_count}</td>
                  <td>{seg.borrower_share_pct}%</td>
                  <td style={{ fontWeight: 600 }}>${seg.total_exposure.toLocaleString()}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ width: '60px', background: 'var(--surface-subtle)', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ width: `${seg.exposure_share_pct}%`, height: '100%', background: 'var(--accent-bronze)' }} />
                      </div>
                      <span>{seg.exposure_share_pct}%</span>
                    </div>
                  </td>
                  <td>{seg.avg_dti}%</td>
                  <td>{seg.avg_credit_score || '—'}</td>
                  <td style={{ color: seg.overdue_amount > 0 ? 'var(--status-red)' : 'inherit', fontWeight: 600 }}>
                    ${seg.overdue_amount.toLocaleString()}
                  </td>
                  <td>
                    <span style={{ color: seg.default_rate > 5 ? 'var(--status-red)' : 'inherit', fontWeight: 600 }}>
                      {seg.default_rate}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Interactive Policy Simulator */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div>
            <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sliders size={18} color="var(--accent-bronze)" />
              Interactive Risk Threshold Simulator
            </h2>
            <div className="card-subtitle">
              Stress-test the portfolio: adjust credit policy cutoffs to observe exposure reclassification before changing policy.
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn btn-outline" onClick={resetSimulation}>
              <RotateCcw size={14} /> Reset
            </button>
            <button className="btn btn-primary" onClick={runSimulation} disabled={simulating}>
              <Play size={14} /> {simulating ? 'Simulating...' : 'Run Simulation'}
            </button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px', padding: '16px 0', borderBottom: '1px solid var(--border-color)', marginBottom: '16px' }}>
          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
              High DTI Threshold: <span style={{ color: 'var(--accent-bronze)' }}>{highDtiPct}%</span>
            </label>
            <input
              type="range"
              min="30"
              max="60"
              step="1"
              value={highDtiPct}
              onChange={e => setHighDtiPct(Number(e.target.value))}
              style={{ width: '100%' }}
            />
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
              DTI ratios at or above this trigger the High DTI risk penalty.
            </div>
          </div>

          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
              Low Credit Score Cutoff: <span style={{ color: 'var(--accent-bronze)' }}>{lowScoreThreshold}</span>
            </label>
            <input
              type="range"
              min="550"
              max="700"
              step="5"
              value={lowScoreThreshold}
              onChange={e => setLowScoreThreshold(Number(e.target.value))}
              style={{ width: '100%' }}
            />
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Scores below this trigger the low score policy penalty.
            </div>
          </div>

          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
              Overdue Days Threshold: <span style={{ color: 'var(--accent-bronze)' }}>{overdueDaysThreshold} days</span>
            </label>
            <input
              type="range"
              min="15"
              max="60"
              step="5"
              value={overdueDaysThreshold}
              onChange={e => setOverdueDaysThreshold(Number(e.target.value))}
              style={{ width: '100%' }}
            />
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Days past due (DPD) triggering delinquency weight.
            </div>
          </div>
        </div>

        {/* Simulation Output */}
        {simResults && (
          <div>
            <h3 style={{ fontSize: '14px', marginBottom: '10px' }}>
              Simulated Portfolio Re-allocation (Total Borrowers: {simResults.total_borrowers})
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
              {simResults.results.map((res: any) => (
                <div key={res.risk_band} style={{ background: 'var(--surface-subtle)', padding: '14px', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <StatusBadge status={res.risk_band} type="risk" />
                    <span style={{ fontSize: '12px', fontWeight: 600 }}>{res.borrower_share_pct}%</span>
                  </div>
                  <div style={{ fontSize: '20px', fontWeight: 700 }}>{res.borrower_count} Borrowers</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Exposure: ${res.exposure_amount.toLocaleString()} ({res.exposure_share_pct}%)
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Credit Score Bands Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Credit Score Bands Deep-Dive</h2>
            <div className="card-subtitle">Performance metrics across Super Prime, Prime, Near Prime, and Subprime</div>
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th scope="col">Credit Score Band</th>
                <th scope="col">Borrower Count</th>
                <th scope="col">Total Loans</th>
                <th scope="col">Total Principal ($)</th>
                <th scope="col">Outstanding ($)</th>
                <th scope="col">Overdue ($)</th>
                <th scope="col">Default Rate (%)</th>
                <th scope="col">Repayment Rate (%)</th>
                <th scope="col">Avg DTI (%)</th>
              </tr>
            </thead>
            <tbody>
              {scoreBands.map((sb: any) => (
                <tr key={sb.band_name}>
                  <td style={{ fontWeight: 600 }}>{sb.band_name}</td>
                  <td>{sb.borrower_count}</td>
                  <td>{sb.total_loans}</td>
                  <td>${sb.total_principal.toLocaleString()}</td>
                  <td style={{ fontWeight: 600 }}>${sb.outstanding_principal.toLocaleString()}</td>
                  <td style={{ color: sb.overdue_amount > 0 ? 'var(--status-red)' : 'inherit', fontWeight: 600 }}>
                    ${sb.overdue_amount.toLocaleString()}
                  </td>
                  <td>
                    <span style={{ color: sb.default_rate > 5 ? 'var(--status-red)' : 'inherit', fontWeight: 600 }}>
                      {sb.default_rate}%
                    </span>
                  </td>
                  <td style={{ color: 'var(--status-green)', fontWeight: 600 }}>{sb.repayment_rate}%</td>
                  <td>{sb.avg_dti}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

