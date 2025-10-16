import { useMemo } from 'react';
import { useDashboardContext } from '../context/DashboardContext.jsx';

function formatCurrency(n) {
  if (n == null) return '$0';
  return `$${Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
}

export default function useAgentPerformance(period = 'Last 90 Days') {
  const { commissions, agentPlans } = useDashboardContext();

  // For iteration 1 we treat period as a label only and use all commissions from context
  const agentsByName = useMemo(() => {
    const map = new Map();
    commissions.forEach((c) => {
      const name = c.broker || c.agent || 'Unknown';
      const plan = agentPlans[name];
      const splitDefault = plan ? (plan.primarySplit.agent / 100) : 0.5; // plan stores percent (70 => 0.7)

      const commissionPercent = (c.grossCommissionRate ?? 0) / 100; // e.g. 2.5 => 0.025
      const gci = (c.salePrice ?? 0) * commissionPercent;
      const agentSplit = (c.finalAgentSplitPercent != null ? c.finalAgentSplitPercent / 100 : null) || (splitDefault || 0.5);
      const agentPayout = gci * agentSplit;

      if (!map.has(name)) {
        map.set(name, {
          name,
          deals: [],
          totalDealVolume: 0,
          totalGci: 0,
          agentPayout: 0,
          avgDealTime: 0,
          dealsInProgress: 0,
          score: 0,
        });
      }

      const row = map.get(name);
      row.deals.push(c);
      row.totalDealVolume += c.salePrice ?? 0;
      row.totalGci += gci;
      row.agentPayout += agentPayout;
      row.score = Math.max(row.score, c.score ?? 0);
      row.dealsInProgress += c.status !== 'Paid' && c.status !== 'Approved' ? 1 : 0;
      row.avgDealTime = Math.round((row.avgDealTime * (row.deals.length - 1) + (c.dealTime ?? 0)) / row.deals.length || 0);
    });

    // convert to array and compute derived
    const arr = Array.from(map.values()).map((a) => ({
      ...a,
      formattedTotalDealVolume: formatCurrency(a.totalDealVolume),
      formattedTotalGci: formatCurrency(a.totalGci),
      formattedAgentPayout: formatCurrency(a.agentPayout),
    }));

    return arr;
  }, [commissions, agentPlans]);

  const brokerageTotals = useMemo(() => {
    const totals = { totalDealVolume: 0, totalGci: 0 };
    agentsByName.forEach((a) => {
      totals.totalDealVolume += a.totalDealVolume;
      totals.totalGci += a.totalGci;
    });
    return {
      ...totals,
      formattedTotalDealVolume: formatCurrency(totals.totalDealVolume),
      formattedTotalGci: formatCurrency(totals.totalGci),
    };
  }, [agentsByName]);

  return {
    agents: agentsByName,
    totals: brokerageTotals,
  };
}
