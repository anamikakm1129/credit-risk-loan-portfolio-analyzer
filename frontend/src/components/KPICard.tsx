import React from 'react';
import { TrendingUp, TrendingDown, Info } from 'lucide-react';

interface KPICardProps {
  label: string;
  value: string | number;
  formattedValue?: string;
  definition?: string;
  period?: string;
  changePct?: number;
  trendDirection?: 'up' | 'down' | 'flat';
  isGoodWhenUp?: boolean;
}

export const KPICard: React.FC<KPICardProps> = ({
  label,
  value,
  formattedValue,
  definition,
  period,
  changePct,
  trendDirection,
  isGoodWhenUp = true,
}) => {
  const displayVal = formattedValue ?? String(value);

  const isUp = trendDirection === 'up' || (changePct && changePct > 0);
  const isDown = trendDirection === 'down' || (changePct && changePct < 0);
  
  // Decide whether upward trend is positive or negative for this metric
  const trendClass = isUp
    ? (isGoodWhenUp ? 'up' : 'down')
    : (isGoodWhenUp ? 'down' : 'up');

  return (
    <div className="kpi-card" role="region" aria-label={label}>
      <div className="kpi-label-row">
        <span className="kpi-label">{label}</span>
        {definition && (
          <span className="info-tip" title={definition} aria-label={`Metric definition: ${definition}`}>
            <Info size={14} />
          </span>
        )}
      </div>
      
      <div className="kpi-value">{displayVal}</div>

      <div className="kpi-meta">
        {changePct !== undefined && (
          <span className={`kpi-trend-badge ${trendClass}`}>
            {isUp ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            {Math.abs(changePct)}%
          </span>
        )}
        {period && <span>{period}</span>}
      </div>
    </div>
  );
};

