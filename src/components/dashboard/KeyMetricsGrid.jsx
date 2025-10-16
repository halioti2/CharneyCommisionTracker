import React from 'react';
import { useCommissionData } from '../../hooks/useCommissionData';
import { formatCurrency } from '../../lib/formatters';

const MetricCard = ({ title, value, description }) => (
  <div className="p-4 bg-white rounded-lg shadow">
    <h3 className="text-sm font-medium text-gray-500">{title}</h3>
    <p className="mt-1 text-3xl font-semibold text-gray-900">{value}</p>
    {description && <p className="text-sm text-gray-500">{description}</p>}
  </div>
);

const KeyMetricsGrid = ({ period }) => {
  const { totalGci, totalDealVolume, dealsInProgress } = useCommissionData({ period });

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <MetricCard
        title="Total GCI"
        value={formatCurrency(totalGci)}
        description="For closed deals in the selected period"
      />
      <MetricCard
        title="Total Deal Volume"
        value={formatCurrency(totalDealVolume)}
        description="Value of all closed transactions"
      />
      <MetricCard
        title="Deals In Progress"
        value={dealsInProgress}
        description="Active and contract-stage deals"
      />
    </div>
  );
};

export default KeyMetricsGrid;
