import React, { useState } from 'react';
import {
  LayoutDashboard,
  Users,
  CreditCard,
  Receipt,
  ShieldAlert,
  GitBranch,
  FileSpreadsheet,
  CheckCircle,
  Settings,
  Search,
  Calendar,
} from 'lucide-react';

// Views
import { DashboardView } from './features/dashboard/DashboardView';
import { BorrowersView } from './features/borrowers/BorrowersView';
import { LoansView } from './features/loans/LoansView';
import { RepaymentsView } from './features/repayments/RepaymentsView';
import { RiskAnalysisView } from './features/risk-analysis/RiskAnalysisView';
import { VintageAnalysisView } from './features/vintage-analysis/VintageAnalysisView';
import { ReportsView } from './features/reports/ReportsView';
import { DataQualityView } from './features/data-quality/DataQualityView';
import { SettingsView } from './features/settings/SettingsView';

// Modals
import { BorrowerDetailModal } from './components/BorrowerDetailModal';
import { LoanDetailModal } from './components/LoanDetailModal';

type NavTab =
  | 'dashboard'
  | 'borrowers'
  | 'loans'
  | 'repayments'
  | 'risk-analysis'
  | 'vintage-analysis'
  | 'reports'
  | 'data-quality'
  | 'settings';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('dashboard');
  const [reportingDate, setReportingDate] = useState<string>('2026-10-19');
  const [globalSearch, setGlobalSearch] = useState<string>('');
  
  // Drill-down states
  const [selectedBorrowerId, setSelectedBorrowerId] = useState<string | null>(null);
  const [selectedLoanId, setSelectedLoanId] = useState<string | null>(null);

  const handleGlobalSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (globalSearch.trim()) {
      setActiveTab('borrowers');
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar" aria-label="Main Navigation">
        <div className="sidebar-header">
          <div className="brand-badge">
            <div className="brand-mark">CV</div>
            <div>
              <div className="brand-name">CredVista</div>
              <div className="brand-subtitle">Risk Intelligence</div>
            </div>
          </div>
        </div>

        <ul className="nav-list" role="menubar">
          <li
            role="menuitem"
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <LayoutDashboard size={20} />
            <span>Dashboard</span>
          </li>

          <li
            role="menuitem"
            className={`nav-item ${activeTab === 'borrowers' ? 'active' : ''}`}
            onClick={() => setActiveTab('borrowers')}
          >
            <Users size={20} />
            <span>Borrowers</span>
          </li>

          <li
            role="menuitem"
            className={`nav-item ${activeTab === 'loans' ? 'active' : ''}`}
            onClick={() => setActiveTab('loans')}
          >
            <CreditCard size={20} />
            <span>Loans</span>
          </li>

          <li
            role="menuitem"
            className={`nav-item ${activeTab === 'repayments' ? 'active' : ''}`}
            onClick={() => setActiveTab('repayments')}
          >
            <Receipt size={20} />
            <span>Repayments</span>
          </li>

          <li
            role="menuitem"
            className={`nav-item ${activeTab === 'risk-analysis' ? 'active' : ''}`}
            onClick={() => setActiveTab('risk-analysis')}
          >
            <ShieldAlert size={20} />
            <span>Risk Analysis</span>
          </li>

          <li
            role="menuitem"
            className={`nav-item ${activeTab === 'vintage-analysis' ? 'active' : ''}`}
            onClick={() => setActiveTab('vintage-analysis')}
          >
            <GitBranch size={20} />
            <span>Vintage Analysis</span>
          </li>

          <li
            role="menuitem"
            className={`nav-item ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => setActiveTab('reports')}
          >
            <FileSpreadsheet size={20} />
            <span>Reports</span>
          </li>

          <li
            role="menuitem"
            className={`nav-item ${activeTab === 'data-quality' ? 'active' : ''}`}
            onClick={() => setActiveTab('data-quality')}
          >
            <CheckCircle size={20} />
            <span>Data Quality</span>
          </li>

          <li
            role="menuitem"
            className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <Settings size={20} />
            <span>Settings</span>
          </li>
        </ul>

        <div className="sidebar-footer">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span style={{ width: '10px', height: '10px', background: 'var(--status-green)', borderRadius: '50%' }} />
            <span style={{ color: 'var(--nav-text)', fontWeight: 600 }}>System Online</span>
          </div>
          <div style={{ fontSize: '12.5px', color: 'var(--nav-text-muted)' }}>
            Ruleset v1.0 • 2026 Policy
          </div>
        </div>
      </aside>

      {/* Main Wrapper */}
      <div className="main-wrapper">
        {/* Top Header */}
        <header className="top-header">
          {/* Global Search */}
          <form onSubmit={handleGlobalSearchSubmit} className="header-search">
            <Search size={18} color="var(--text-muted)" />
            <input
              type="text"
              placeholder="Search borrower or loan ID across portfolio..."
              value={globalSearch}
              onChange={e => setGlobalSearch(e.target.value)}
              aria-label="Global portfolio search"
            />
          </form>

          {/* Right Header Actions */}
          <div className="header-actions">
            {/* Reporting Date Selector */}
            <div className="date-selector">
              <Calendar size={16} color="var(--accent-bronze)" />
              <label htmlFor="reporting-date-picker" style={{ fontWeight: 600, fontSize: '13.5px' }}>
                As of:
              </label>
              <input
                id="reporting-date-picker"
                type="date"
                value={reportingDate}
                onChange={e => setReportingDate(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', paddingLeft: '10px', borderLeft: '1px solid var(--border-color)' }}>
              <div
                style={{
                  width: '38px',
                  height: '38px',
                  borderRadius: '50%',
                  background: 'var(--surface-subtle)',
                  border: '1px solid var(--border-color)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700,
                  fontSize: '14px',
                  color: 'var(--accent-bronze)',
                }}
                title="Credit Risk Officer (Analyst Role)"
              >
                CR
              </div>
            </div>
          </div>
        </header>

        {/* Content Body */}
        <main className="content-body" tabIndex={-1}>
          {activeTab === 'dashboard' && (
            <DashboardView
              reportingDate={reportingDate}
              onSelectBorrower={id => setSelectedBorrowerId(id)}
              onSelectLoan={id => setSelectedLoanId(id)}
              onNavigate={tab => setActiveTab(tab as NavTab)}
            />
          )}

          {activeTab === 'borrowers' && (
            <BorrowersView
              reportingDate={reportingDate}
              onSelectBorrower={id => setSelectedBorrowerId(id)}
              initialSearch={globalSearch}
              onNavigate={tab => setActiveTab(tab as NavTab)}
            />
          )}

          {activeTab === 'loans' && (
            <LoansView
              reportingDate={reportingDate}
              onSelectLoan={id => setSelectedLoanId(id)}
              onSelectBorrower={id => setSelectedBorrowerId(id)}
            />
          )}

          {activeTab === 'repayments' && (
            <RepaymentsView
              reportingDate={reportingDate}
              onSelectLoan={id => setSelectedLoanId(id)}
            />
          )}

          {activeTab === 'risk-analysis' && (
            <RiskAnalysisView reportingDate={reportingDate} />
          )}

          {activeTab === 'vintage-analysis' && (
            <VintageAnalysisView reportingDate={reportingDate} />
          )}

          {activeTab === 'reports' && (
            <ReportsView reportingDate={reportingDate} />
          )}

          {activeTab === 'data-quality' && (
            <DataQualityView />
          )}

          {activeTab === 'settings' && (
            <SettingsView />
          )}
        </main>
      </div>

      {/* Drilldown Modals */}
      <BorrowerDetailModal
        borrowerId={selectedBorrowerId}
        onClose={() => setSelectedBorrowerId(null)}
        reportingDate={reportingDate}
      />

      <LoanDetailModal
        loanId={selectedLoanId}
        onClose={() => setSelectedLoanId(null)}
        reportingDate={reportingDate}
      />
    </div>
  );
};

export default App;
