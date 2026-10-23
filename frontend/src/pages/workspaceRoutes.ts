export const workspaceRoutes = [
  {
    path: '/app',
    title: 'Overview',
    phase: 'Phase 06',
    action: 'Run a check',
    description:
      'Priorities will appear here once authorized checks and the finding engine are implemented.',
    empty: 'A clear starting point. Soon.',
  },
  {
    path: '/app/assets',
    title: 'Assets',
    phase: 'Phase 03',
    action: 'Add domain',
    description:
      'Domain ownership verification will be required before any external checks become available.',
    empty: 'Your domains will start here.',
  },
  {
    path: '/app/findings',
    title: 'Findings',
    phase: 'Phase 05',
    action: 'Run a check',
    description:
      'Evidence-backed findings and recommended actions will be available after the checking and prioritization phases.',
    empty: 'Evidence comes before findings.',
  },
  {
    path: '/app/tasks',
    title: 'Action plan',
    phase: 'Phase 06',
    action: 'Create action',
    description:
      'Remediation tasks, owner labels and progress tracking are planned. There are no saved tasks yet.',
    empty: 'Room for your next action.',
  },
  {
    path: '/app/reports',
    title: 'Reports',
    phase: 'Phase 07',
    action: 'Generate report',
    description:
      'Management PDF reports will use stored evidence. Report generation is not available yet.',
    empty: 'A report starts with real evidence.',
  },
];
