import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { Settings as SettingsIcon, BookOpen, Shield, Code, Check } from 'lucide-react';

export const SettingsView: React.FC = () => {
  const [ruleSet, setRuleSet] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getRiskRules()
      .then(res => {
        setRuleSet(res);
        setLoading(false);
      })
      .catch(console.error);
  }, []);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings & Policy Configuration</h1>
          <p className="page-description">
            Versioned risk ruleset definitions, calculation formulas, and analytical methodology standards.
          </p>
        </div>
      </div>

      {/* Active Ruleset Card */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div>
            <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Shield size={18} color="var(--accent-bronze)" />
              Active Risk Ruleset: {ruleSet?.version || 'v1.0'}
            </h2>
            <div className="card-subtitle">
              Status: Active | Effective From: {ruleSet?.effective_from || '2026-01-01'}
            </div>
          </div>
          <span className="badge badge-low">
            <Check size={12} /> Active in Production
          </span>
        </div>

        <p style={{ fontSize: '13.5px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
          {ruleSet?.description || 'Standard Baseline Risk Ruleset v1.0 — 2026 Policy'}
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
          <div style={{ background: 'var(--surface-subtle)', padding: '14px', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>High DTI Policy Cutoff</div>
            <div style={{ fontSize: '18px', fontWeight: 700, margin: '4px 0' }}>
              &ge; {ruleSet?.configuration?.high_dti_pct ?? 43}%
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Weight Penalty: +{ruleSet?.configuration?.high_dti_weight ?? 35} pts
            </div>
          </div>

          <div style={{ background: 'var(--surface-subtle)', padding: '14px', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Low Credit Score Cutoff</div>
            <div style={{ fontSize: '18px', fontWeight: 700, margin: '4px 0' }}>
              &lt; {ruleSet?.configuration?.low_score_threshold ?? 620}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Weight Penalty: +{ruleSet?.configuration?.low_score_weight ?? 40} pts
            </div>
          </div>

          <div style={{ background: 'var(--surface-subtle)', padding: '14px', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Overdue Delinquency Cutoff</div>
            <div style={{ fontSize: '18px', fontWeight: 700, margin: '4px 0' }}>
              &ge; {ruleSet?.configuration?.overdue_days_threshold ?? 30} days
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Weight Penalty: +{ruleSet?.configuration?.overdue_weight ?? 45} pts
            </div>
          </div>
        </div>
      </div>

      {/* Metric Definitions Dictionary */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BookOpen size={18} color="var(--accent-bronze)" />
              CredVista Metric Definitions & Traceability Standards
            </h2>
            <div className="card-subtitle">Reconciled against PRD Section 6 formulas</div>
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th scope="col" style={{ width: '22%' }}>Metric Name</th>
                <th scope="col" style={{ width: '38%' }}>Mathematical Formula</th>
                <th scope="col">Traceability & Policy Rule</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ fontWeight: 600 }}>Outstanding Principal</td>
                <td><code>&Sigma; Remaining Principal Balance for in-scope loans</code></td>
                <td>Excludes settled/closed facilities unless historical exposure view is explicitly toggled.</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600 }}>Overdue Amount</td>
                <td><code>&Sigma; Unpaid amounts past due as of reporting cutoff</code></td>
                <td>Allocates customer payments using FIFO against earliest scheduled due dates.</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600 }}>Default Rate</td>
                <td><code>Defaulted loans / Eligible loans in scope &times; 100</code></td>
                <td>Classified as Default when status is Defaulted or Days Past Due (DPD) &ge; 90 days.</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600 }}>Repayment Rate</td>
                <td><code>Total Amount Collected / Total Amount Due &times; 100</code></td>
                <td>Measures cash realization against scheduled due dates up to reporting cutoff date.</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600 }}>Debt-to-Income (DTI)</td>
                <td><code>(Monthly Debt Obligations / Gross Monthly Income) &times; 100</code></td>
                <td>Uses consistent annualized to monthly income frequency. Null if unverified.</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600 }}>Vintage Default Rate</td>
                <td><code>Cohort Defaults at Age M / Originated Cohort Population</code></td>
                <td>Immature cohorts with observation period &lt; milestone are marked non-observable, never zero.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
