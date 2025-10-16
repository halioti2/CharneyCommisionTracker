// src/mocks/dashboardMockData.js

export const agents = [
  {
    id: 1,
    name: 'John Doe',
    deals: [
      { id: 101, stage: 'Closed', closeDate: '2025-09-15', value: 500000, gci: 15000 },
      { id: 102, stage: 'Contract', value: 750000, gci: 22500 },
      { id: 103, stage: 'Active', value: 600000, gci: 18000 },
      { id: 104, stage: 'Closed', closeDate: '2025-08-20', value: 450000, gci: 13500 },
    ],
  },
  {
    id: 2,
    name: 'Jane Smith',
    deals: [
      { id: 201, stage: 'Closed', closeDate: '2025-09-05', value: 800000, gci: 24000 },
      { id: 202, stage: 'Closed', closeDate: '2025-07-10', value: 650000, gci: 19500 },
      { id: 203, stage: 'Lead', value: 900000, gci: 27000 },
    ],
  },
  {
    id: 3,
    name: 'Mike Johnson',
    deals: [
        { id: 301, stage: 'Closed', closeDate: '2025-09-25', value: 1200000, gci: 36000 },
        { id: 302, stage: 'Contract', value: 300000, gci: 9000 },
    ],
  },
];

export const brokerageData = {
  // This can be calculated from the agents data or be a separate object.
  // For now, we can aggregate it on the fly in our hooks/components.
};
