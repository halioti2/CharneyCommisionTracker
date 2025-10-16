import React, { useMemo } from 'react';
import { FunnelChart, Funnel, Tooltip, LabelList, ResponsiveContainer } from 'recharts';
import { useCommissionData } from '../../hooks/useCommissionData';

const DealPipelineFunnel = ({ period }) => {
  const { agents } = useCommissionData({ period });

  const pipelineData = useMemo(() => {
    const stages = { 'Lead': 0, 'Active': 0, 'Contract': 0, 'Closed': 0 };
    
    agents.flatMap(a => a.deals).forEach(deal => {
      if (stages.hasOwnProperty(deal.stage)) {
        stages[deal.stage]++;
      }
    });

    return Object.keys(stages).map(key => ({ name: key, value: stages[key] }));
  }, [agents]);

  return (
    <div className="p-4 bg-white rounded-lg shadow mb-6">
      <h2 className="text-xl font-bold mb-4">Deal Pipeline Overview</h2>
      <ResponsiveContainer width="100%" height={300}>
        <FunnelChart>
          <Tooltip />
          <Funnel
            dataKey="value"
            data={pipelineData}
            isAnimationActive
          >
            <LabelList position="right" fill="#000" stroke="none" dataKey="name" />
          </Funnel>
        </FunnelChart>
      </ResponsiveContainer>
    </div>
  );
};

export default DealPipelineFunnel;
