import type { Organization } from './authApi';
import type { Finding, FindingPage } from './findingApi';
export type TaskStatus = 'todo' | 'in_progress' | 'done';
export type Task = {
  id: string;
  finding_id: string;
  status: TaskStatus;
  owner_label: string;
  note: string;
  version: number;
  created_at: number;
  updated_at: number;
  completed_at: number | null;
  history_truncated: boolean;
  reopened_at: number | null;
  finding: Finding;
};
export type TaskEvent = {
  id: string;
  actor_id: string;
  actor_label: string;
  version: number;
  kind: string;
  created_at: number;
  changes: Record<string, { old: string; new: string }>;
};
export type TaskDetail = Task & { history: TaskEvent[] };
export type TaskPage = {
  items: Task[];
  total: number;
  offset: number;
  limit: number;
  domains: { id: string; hostname: string }[];
};
export type DashboardData = {
  organization: Organization;
  generated_at: number;
  asset_count: number;
  verified_assets: number;
  eligible_assets: number;
  task_counts: Partial<Record<TaskStatus, number>>;
  done_unverified: number;
  recent_scan_count: number;
  last_useful_observation_at: number | null;
  findings: FindingPage;
  tasks: Task[];
  scans: {
    id: string;
    asset_id: string;
    hostname: string;
    status: string;
    created_at: number;
    finished_at: number | null;
    completed_checks: number;
  }[];
  activity: {
    task_id: string;
    title: string;
    kind: string;
    version: number;
    created_at: number;
    actor_label: string;
  }[];
};
export const statusLabel: Record<TaskStatus, string> = {
  todo: 'To do',
  in_progress: 'In progress',
  done: 'Done by a person',
};
