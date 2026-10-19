import React from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, HelpCircle } from 'lucide-react';

interface StatusBadgeProps {
  status: string;
  type?: 'risk' | 'loan' | 'repayment';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, type = 'risk' }) => {
  const norm = status ? status.toLowerCase() : 'unknown';

  let badgeClass = 'badge-neutral';
  let Icon = HelpCircle;

  if (norm.includes('low') || norm.includes('active') || norm.includes('current') || norm.includes('paid') || norm.includes('completed')) {
    badgeClass = 'badge-low';
    Icon = CheckCircle2;
  } else if (norm.includes('medium') || norm.includes('warning') || norm.includes('late') || norm.includes('partial')) {
    badgeClass = 'badge-medium';
    Icon = AlertTriangle;
  } else if (norm.includes('high') || norm.includes('critical') || norm.includes('delinquent') || norm.includes('defaulted') || norm.includes('failed')) {
    badgeClass = 'badge-high';
    Icon = AlertCircle;
  } else if (norm.includes('review')) {
    badgeClass = 'badge-review';
    Icon = HelpCircle;
  }

  return (
    <span className={`badge ${badgeClass}`} title={`${type}: ${status}`}>
      <Icon size={12} strokeWidth={2.5} aria-hidden="true" />
      <span>{status}</span>
    </span>
  );
};
