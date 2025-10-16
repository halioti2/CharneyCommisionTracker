import { useMemo } from 'react';
import { agents as mockAgents } from '../mocks/dashboardMockData';

// This hook will eventually fetch and process real data.
// For now, it processes the mock data.
export const useCommissionData = ({ period }) => {
  const processedData = useMemo(() => {
    // NOTE: The date filtering logic is not yet implemented.
    // This will be added in the interactivity phase.

    const totalGci = mockAgents.flatMap(a => a.deals)
      .filter(d => d.stage === 'Closed')
      .reduce((sum, d) => sum + d.gci, 0);

    const totalDealVolume = mockAgents.flatMap(a => a.deals)
      .filter(d => d.stage === 'Closed')
      .reduce((sum, d) => sum + d.value, 0);
      
    const dealsInProgress = mockAgents.flatMap(a => a.deals)
        .filter(d => d.stage !== 'Closed' && d.stage !== 'Lead').length;

    return {
      totalGci,
      totalDealVolume,
      dealsInProgress,
      agents: mockAgents, // Pass through the raw agent data for other components
    };
  }, [period]); // Dependency array will be used for filtering later

  return processedData;
};
