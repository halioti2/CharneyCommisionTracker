import React from 'react';
import DateRangeSelector from '../DateRangeSelector';

const DashboardHeader = ({ period, onPeriodChange }) => {
  return (
    <div className="flex items-center justify-between mb-6">
      <h1 className="text-3xl font-black">Commission Dashboard</h1>
      <DateRangeSelector value={period} onChange={onPeriodChange} />
    </div>
  );
};

export default DashboardHeader;
