export type Role = 'USER' | 'ADMIN';

export interface User {
  id: number;
  email: string;
  role: Role;
}

export type TaskType = 'daily' | 'one-time';
export type TaskStatus = 'draft' | 'pending' | 'active' | 'in_progress' | 'completed' | 'approved' | 'rejected';
export type CompletionStatus = 'pending' | 'approved' | 'rejected';

export interface PendingTask {
  id: number;
  title: string;
  description: string;
  type: TaskType;
  points: number;
  status: TaskStatus;
  suggested_by?: {
    id: number;
    email: string;
  };
  created_by?: number;
  requires_review: boolean;
  created_at: string;
}

export interface Task {
  id: number;
  title: string;
  description: string;
  type: TaskType;
  points: number;
  status: TaskStatus;
  suggested_by?: number;
  created_by?: number;
  requires_review: boolean;
  is_personal: boolean;
  deadline?: string; // ISO date string
  created_at: string;
  approved_at?: string;
}

export interface TaskCompletion {
  id: number;
  task_id: number;
  user_id: number;
  task?: Task;
  started_at?: string;
  completed_at?: string;
  time_spent: number;
  proof?: string;
  proof_image_url?: string;
  status: CompletionStatus;
  admin_comment?: string;
  points_awarded?: number;
  created_at: string;
  reviewed_at?: string;
}

export interface Notification {
  id: number;
  user_id: number;
  type: 'task_approved' | 'task_rejected' | 'completion_approved' | 'completion_rejected' | 'reward_approved' | 'reward_rejected' | 'daily_reminder';
  title: string;
  message: string;
  related_id?: number;
  is_read: boolean;
  created_at: string;
}

export interface Reward {
  id: number;
  title: string;
  description: string;
  cost: number;
  status: 'proposed' | 'active';
  suggested_by?: number;
  approved_by?: number;
  created_at: string;
  approved_at?: string;
}

export interface RewardRequest {
  id: number;
  reward_id: number;
  user_id: number;
  reward?: Reward;
  status: 'pending' | 'approved' | 'rejected';
  admin_comment?: string;
  points_spent?: number;
  created_at: string;
  reviewed_at?: string;
}

export interface PointsHistory {
  id: number;
  user_id: number;
  amount: number;
  source: string;
  description?: string;
  created_at: string;
}

export interface UserDashboard {
  balance: number;
  stats: {
    total_earned: number;
    total_spent: number;
    tasks_completed: number;
    tasks_pending_review: number;
  };
  active_completions: TaskCompletion[];
  pending_tasks: Task[];
  completed_tasks: TaskCompletion[];
  recent_history: PointsHistory[];
}

export interface AdminDashboardStats {
  users: {
    total: number;
    admins: number;
    regular: number;
  };
  tasks: {
    total: number;
    active: number;
    draft: number;
  };
  completions: {
    total: number;
    pending: number;
    approved: number;
    rejected: number;
  };
  points: {
    total_awarded: number;
    total_redeemed: number;
  };
  rewards: {
    total: number;
    active: number;
    proposed: number;
    pending_requests: number;
  };
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
