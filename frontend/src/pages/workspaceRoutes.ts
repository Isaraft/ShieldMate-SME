export const workspaceRoutes = [
  {
    path: '/app',
    title: 'Overview',
    phase: 'Phase 06',
    action: 'Run a check',
    description:
      'This public preview shows structure only. Sign in to review your organization’s saved priorities.',
    empty: 'A clear starting point. Soon.',
  },
  {
    path: '/app/assets',
    title: 'Assets',
    phase: 'Phase 03',
    action: 'Add domain',
    description:
      'Domain enrollment and DNS ownership verification are available in your signed-in workspace. This preview cannot send verification requests.',
    empty: 'Your domains will start here.',
  },
  {
    path: '/app/findings',
    title: 'Findings',
    phase: 'Phase 05',
    action: 'Run a check',
    description:
      'Findings in your workspace use saved authorized evidence. No assessment data is loaded in this preview.',
    empty: 'Evidence comes before findings.',
  },
  {
    path: '/app/tasks',
    title: 'Action plan',
    phase: 'Phase 06',
    action: 'Create action',
    description:
      'Sign in to create and track remediation tasks. This screen is a read-only layout preview.',
    empty: 'Room for your next action.',
  },
  {
    path: '/app/reports',
    title: 'Reports',
    phase: 'Phase 07',
    action: 'Generate report',
    description:
      'Sign in to generate reports from persisted evidence. This preview cannot generate customer PDFs.',
    empty: 'A report starts with real evidence.',
  },
];
