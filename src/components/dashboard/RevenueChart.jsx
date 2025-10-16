import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useCommissionData } from '../../hooks/useCommissionData';
import { formatCurrency } from '../../lib/formatters';

const RevenueChart = ({ period }) => {
  const { agents } = useCommissionData({ period });

  const chartData = agents.map(agent => ({
    name: agent.name,
    gci: agent.deals.filter(d => d.stage === 'Closed').reduce((sum, d) => sum + d.gci, 0),
  }));

  return (
    <div className="p-4 bg-white rounded-lg shadow mb-6">
      <h2 className="text-xl font-bold mb-4">GCI by Agent</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis tickFormatter={(value) => formatCurrency(value, 0)} />
          <Tooltip formatter={(value) => formatCurrency(value)} />
          <Legend />
          <Bar dataKey="gci" fill="#8884d8" name="Gross Commission Income" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RevenueChart;
