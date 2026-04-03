import api from './api';
import {
  Task,
  PendingTask,
  TaskCompletion,
  Reward,
  RewardRequest,
  AdminDashboardStats,
} from '../types';

export interface ModerationData {
  comment?: string;
}

export interface PointsAdjustmentData {
  user_id: number;
  amount: number;
  reason: string;
}

export const adminApi = {
  // Pending task suggestions (moderation)
  getPendingTasks: (): Promise<PendingTask[]> =>
    api.get('/admin/pending-tasks').then(r => r.data),

  approveTaskSuggestion: (taskId: number, data?: ModerationData): Promise<void> =>
    api.post(`/admin/pending-tasks/${taskId}/approve`, data || {}).then(r => r.data),

  rejectTaskSuggestion: (taskId: number, data?: ModerationData): Promise<void> =>
    api.post(`/admin/pending-tasks/${taskId}/reject`, data || {}).then(r => r.data),

  // Task completions moderation
  getPendingCompletions: (): Promise<TaskCompletion[]> =>
    api.get('/admin/completions?status=completed').then(r => r.data),

  approveCompletion: (completionId: number, data?: ModerationData): Promise<void> =>
    api.post(`/admin/completions/${completionId}/approve`, data || {}).then(r => r.data),

  rejectCompletion: (completionId: number, data?: ModerationData): Promise<void> =>
    api.post(`/admin/completions/${completionId}/reject`, data || {}).then(r => r.data),

  // Pending rewards (proposed by users)
  getPendingRewards: (): Promise<Reward[]> =>
    api.get('/admin/rewards?status=proposed').then(r => r.data),

  approveReward: (rewardId: number): Promise<void> =>
    api.put(`/admin/rewards/${rewardId}`, { status: 'active' }).then(r => r.data),

  rejectReward: (rewardId: number): Promise<void> =>
    api.delete(`/admin/rewards/${rewardId}`).then(r => r.data),

  // Reward redemption requests
  getRewardRequests: (status?: string): Promise<RewardRequest[]> =>
    api.get('/admin/reward-requests', { params: { status } }).then(r => r.data),

  approveRewardRequest: (requestId: number, data?: ModerationData): Promise<void> =>
    api.post(`/admin/reward-requests/${requestId}/approve`, data || {}).then(r => r.data),

  rejectRewardRequest: (requestId: number, data?: ModerationData): Promise<void> =>
    api.post(`/admin/reward-requests/${requestId}/reject`, data || {}).then(r => r.data),

  // Statistics
  getDashboardStats: (): Promise<AdminDashboardStats> =>
    api.get('/admin/stats/dashboard').then(r => r.data),

  // User management
  getUsers: (): Promise<Array<{id: number; email: string; role: string; balance: number}>> =>
    api.get('/admin/users').then(r => r.data),

  getUserDetails: (userId: number): Promise<any> =>
    api.get(`/admin/users/${userId}/details`).then(r => r.data),

  // Points management
  adjustPoints: (data: PointsAdjustmentData): Promise<void> =>
    api.post('/admin/points/adjust', data).then(r => r.data),
};
