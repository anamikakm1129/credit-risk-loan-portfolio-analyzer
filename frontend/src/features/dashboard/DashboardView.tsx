import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { KPICard } from '../../components/KPICard';
import { StatusBadge } from '../../components/StatusBadge';
import { AlertTriangle, TrendingUp, ShieldCheck, ArrowRight, Info } from 'lucide-react';

interface DashboardViewProps {
  reportingDate: string;
  onSelectBorrower: (id: string) => void;
  onSelectLoan: (id: string) => void;
  onNavigate: (tab: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  reportingDate,
  onSelectBorrower,
  onSelectLoan,
  onNavigate,
}) => {
  const [summary, setSummary] = useState<any>(null);
  const [trends, setTrends] = useState<any[]>([]);
  const [riskSegments, setRiskSegments] = useState<any>(null);
  const [scoreBands, setScoreBands] = useState<any[]>([]);
  const [highRiskBorrowers, setHighRiskBorrowers] = useState<any[]>([]);
  const [recentLoans, setRecentLoans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.getDashboardSummary(reportingDate),
      api.getDashboardTrends(reportingDate),
      api.getRiskSegments(reportingDate),
      api.getCreditScoreBands(reportingDate),
      api.getBorrowers({ risk_band: 'High', page_size: 5, reporting_date: reportingDate }),
      api.getLoans({ page_size: 5, reporting_date: reportingDate, sort_by: 'issue_date', sort_dir: 'desc' }),
    ]).then(([sumRes, trendRes, riskRes, bandsRes, bRes, lRes]) => {
      setSummary(sumRes);
      setTrends(trendRes.monthly_trends || []);
      setRiskSegments(riskRes);
      setScoreBands(bandsRes.bands || []);
      setHighRiskBorrowers(bRes.items || []);
      setRecentLoans(lRes.items || []);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, [reportingDate]);

  if (loading && !summary) {
    return (
      <div className="empty-state">
        <div className="skeleton" style={{ height: '32px', width: '240px', marginBottom: '24px' }} />
        <div className="kpi-grid">
          {[1, 2, 3, 4].map(n => (
            <div key={n} className="skeleton" style={{ height: '110px' }} />
          ))}
        </div>
        <div className="skeleton" style={{ height: '300px' }} />
      </div>
    );
  }

  const maxTrendPrincipal = Math.max(...trends.map(t => t.outstanding_principal), 1000);
  const maxBandBorrowers = Math.max(...scoreBands.map(b => b.borrower_count), 1);

  return (
    <div>
      {/* Page Title & Subtitle */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Portfolio Health & Risk Overview</h1>
          <p className="page-description">
            Consolidated credit risk indicators, exposure tracking, and segment health under Ruleset {summary?.active_rule_version || 'v1.0'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-secondary" onClick={() => onNavigate('reports')}>
            Generate Report
          </button>
          <button className="btn btn-primary" onClick={() => onNavigate('risk-analysis')}>
            Configure Risk Rules
          </button>
        </div>
      </div>

      {/* PRD F-01: 4 Core Headline KPI Cards */}
      <div className="kpi-grid">
        <KPICard
          label={summary.total_loans.label}
          value={summary.total_loans.value}
          formattedValue={summary.total_loans.formatted_value}
          definition={summary.total_loans.definition}
          period={summary.total_loans.period}
          changePct={summary.total_loans.change_pct}
          trendDirection={summary.total_loans.trend_direction}
          isGoodWhenUp={true}
        />

        <KPICard
          label={summary.outstanding_principal.label}
          value={summary.outstanding_principal.value}
          formattedValue={summary.outstanding_principal.formatted_value}
          definition={summary.outstanding_principal.definition}
          period={summary.outstanding_principal.period}
          changePct={summary.outstanding_principal.change_pct}
          trendDirection={summary.outstanding_principal.trend_direction}
          isGoodWhenUp={false}
        />

        <KPICard
          label={summary.default_rate.label}
          value={summary.default_rate.value}
          formattedValue={summary.default_rate.formatted_value}
          definition={summary.default_rate.definition}
          period={summary.default_rate.period}
          changePct={summary.default_rate.change_pct}
          trendDirection={summary.default_rate.trend_direction}
          isGoodWhenUp={false}
        />

        <KPICard
          label={summary.overdue_amount.label}
          value={summary.overdue_amount.value}
          formattedValue={summary.overdue_amount.formatted_value}
          definition={summary.overdue_amount.definition}
          period={summary.overdue_amount.period}
          changePct={summary.overdue_amount.change_pct}
          trendDirection={summary.overdue_amount.trend_direction}
          isGoodWhenUp={false}
        />
      </div>

      {/* Secondary Quick Metrics Strip */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <div style={{ background: 'var(--surface-card)', border: '1px solid var(--border-color)', padding: '10px 16px', borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
          <span style={{ color: 'var(--text-muted)' }}>Repayment Collection Rate:</span>
          <strong style={{ color: 'var(--status-green)' }}>{summary.repayment_rate.formatted_value}</strong>
        </div>
        <div style={{ background: 'var(--surface-card)', border: '1px solid var(--border-color)', padding: '10px 16px', borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
          <span style={{ color: 'var(--text-muted)' }}>Weighted Avg DTI:</span>
          <strong>{summary.weighted_avg_dti.formatted_value}</strong>
        </div>
        <div style={{ background: 'var(--surface-card)', border: '1px solid var(--border-color)', padding: '10px 16px', borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
          <span style={{ color: 'var(--text-muted)' }}>Weighted Avg Credit Score:</span>
          <strong>{summary.weighted_avg_credit_score.formatted_value}</strong>
        </div>
        <div style={{ background: 'var(--surface-card)', border: '1px solid var(--border-color)', padding: '10px 16px', borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
          <span style={{ color: 'var(--text-muted)' }}>Active Borrowers in Scope:</span>
          <strong>{summary.active_borrowers_count}</strong>
        </div>
      </div>

      {/* Middle Row: Focused Visualizations */}
      <div className="charts-grid-3">
        {/* Chart 1: Monthly Portfolio Trend */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Portfolio Exposure Trend</h2>
              <div className="card-subtitle">Outstanding balance ($) across cohorts</div>
            </div>
          </div>
          <div style={{ height: '180px', display: 'flex', alignItems: 'flex-end', gap: '12px', padding: '10px 0' }}>
            {trends.slice(-8).map((t, idx) => {
              const heightPct = Math.round((t.outstanding_principal / maxTrendPrincipal) * 100);
              return (
                <div key={idx} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'flex-end' }}>
                  <div
                    style={{
                      width: '100%',
                      background: 'linear-gradient(180deg, #9C7A4A 0%, #B8925A 100%)',
                      height: `${Math.max(8, heightPct)}%`,
                      borderRadius: '4px 4px 0 0',
                      transition: 'height 0.3s ease',
                    }}
                    title={`${t.period}: $${t.outstanding_principal.toLocaleString()} outstanding, ${t.loan_count} loans`}
                  />
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '6px' }}>
                    {t.period.slice(2)}
                  </span>
                </div>
              );
            })}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center', marginTop: '8px' }}>
            Hover bars for monthly cohort balance & count
          </div>
        </div>

        {/* Chart 2: Credit Score Distribution */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Credit Score Bands</h2>
              <div className="card-subtitle">Borrowers per score classification</div>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', height: '180px', justifyContent: 'center' }}>
            {scoreBands.map((sb, idx) => {
              const widthPct = Math.round((sb.borrower_count / maxBandBorrowers) * 100);
              return (
                <div key={idx}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11.5px', marginBottom: '3px' }}>
                    <span style={{ fontWeight: 500 }}>{sb.band_name.split(' ')[0]}</span>
                    <span style={{ color: 'var(--text-muted)' }}>{sb.borrower_count} ({sb.default_rate}% def)</span>
                  </div>
                  <div style={{ width: '100%', background: 'var(--surface-subtle)', height: '7px', borderRadius: '4px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${widthPct}%`,
                        height: '100%',
                        background: idx < 2 ? 'var(--status-green)' : (idx === 2 ? 'var(--status-amber)' : 'var(--status-red)'),
                        borderRadius: '4px',
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center', marginTop: '8px' }}>
            FICO score ranges: 300 to 850
          </div>
        </div>

        {/* Chart 3: Risk Segmentation Share */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Risk Segmentation Share</h2>
              <div className="card-subtitle">Rule v1.0 exposure allocation</div>
            </div>
            <button className="btn btn-outline" style={{ padding: '2px 8px', fontSize: '11px' }} onClick={() => onNavigate('risk-analysis')}>
              View All
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', height: '180px', justifyContent: 'center' }}>
            {riskSegments?.segments?.map((seg: any, idx: number) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <StatusBadge status={seg.risk_band} type="risk" />
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    {seg.borrower_count} borrowers
                  </span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>${(seg.total_exposure / 1000).toFixed(0)}k</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{seg.exposure_share_pct}% share</div>
                </div>
              </div>
            ))}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center', marginTop: '8px' }}>
            Deterministic rule segmentation — not opaque ML
          </div>
        </div>
      </div>

      {/* Lower Row: Top High-Risk Borrowers and Recent Loan Activity */}
      <div className="charts-grid-2">
        {/* Table 1: High Risk Borrowers */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertTriangle size={16} color="var(--status-red)" />
                High-Risk Borrowers Requiring Attention
              </h2>
              <div className="card-subtitle">Borrowers flagged by elevated DTI, score, or overdue payments</div>
            </div>
            <button className="btn btn-outline" style={{ fontSize: '12px', padding: '4px 10px' }} onClick={() => onNavigate('borrowers')}>
              Full Directory <ArrowRight size={12} />
            </button>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th scope="col">ID / Name</th>
                  <th scope="col">Score</th>
                  <th scope="col">DTI</th>
                  <th scope="col">Exposure</th>
                  <th scope="col">Overdue</th>
                  <th scope="col">Action</th>
                </tr>
              </thead>
              <tbody>
                {highRiskBorrowers.map((b: any) => (
                  <tr key={b.borrower_id} style={{ cursor: 'pointer' }} onClick={() => onSelectBorrower(b.borrower_id)}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{b.borrower_id}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{b.full_name}</div>
                    </td>
                    <td>{b.credit_score ?? 'Missing'}</td>
                    <td>{b.dti_ratio ? `${b.dti_ratio}%` : '—'}</td>
                    <td style={{ fontWeight: 600 }}>${b.total_exposure.toLocaleString()}</td>
                    <td style={{ color: b.total_overdue > 0 ? 'var(--status-red)' : 'inherit', fontWeight: 600 }}>
                      ${b.total_overdue.toLocaleString()}
                    </td>
                    <td>
                      <button className="btn btn-outline" style={{ padding: '3px 8px', fontSize: '11px' }}>
                        Profile
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Table 2: Recent Loan Activity */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Recent Loan Originations</h2>
              <div className="card-subtitle">Latest issued loans across the portfolio</div>
            </div>
            <button className="btn btn-outline" style={{ fontSize: '12px', padding: '4px 10px' }} onClick={() => onNavigate('loans')}>
              All Loans <ArrowRight size={12} />
            </button>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th scope="col">Loan ID</th>
                  <th scope="col">Borrower</th>
                  <th scope="col">Principal</th>
                  <th scope="col">Rate</th>
                  <th scope="col">Status</th>
                  <th scope="col">Action</th>
                </tr>
              </thead>
              <tbody>
                {recentLoans.map((l: any) => (
                  <tr key={l.loan_id} style={{ cursor: 'pointer' }} onClick={() => onSelectLoan(l.loan_id)}>
                    <td style={{ fontWeight: 600 }}>{l.loan_id}</td>
                    <td>{l.borrower_name}</td>
                    <td style={{ fontWeight: 600 }}>${l.principal_amount.toLocaleString()}</td>
                    <td>{(l.annual_rate * 100).toFixed(1)}%</td>
                    <td>
                      <StatusBadge status={l.status} type="loan" />
                    </td>
                    <td>
                      <button className="btn btn-outline" style={{ padding: '3px 8px', fontSize: '11px' }}>
                        Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
