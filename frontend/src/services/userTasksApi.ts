import api from './api';
import {
  Task,
  TaskCompletion,
  TaskType,
  UserDashboard,
  Notification,
} from '../types';

export interface SuggestTaskData {
  title: string;
  description: string;
  type: TaskType;
  points: number;
  requires_review?: boolean;
}

export interface CompleteTaskData {
  proof: string;
  proof_image_url?: string;
  time_spent?: number;
}

export const userTasksApi = {
  // Task suggestions
  suggestTask: (data: SuggestTaskData): Promise<Task> =>
    api.post('/user/suggest', data).then(r => r.data),

  // Get user's tasks
  getMyActive: (): Promise<TaskCompletion[]> =>
    api.get('/user/my-active').then(r => r.data),

  getMyPending: (): Promise<Task[]> =>
    api.get('/user/my-pending').then(r => r.data),

  getMyCompleted: (): Promise<TaskCompletion[]> =>
    api.get('/user/my-completed').then(r => r.data),

  getMyAwaitingReview: (): Promise<TaskCompletion[]> =>
    api.get('/user/my-awaiting-review').then(r => r.data),

  // Task execution
  startTask: (taskId: number): Promise<TaskCompletion> =>
    api.post(`/user/${taskId}/start`).then(r => r.data),

  completeTask: (taskId: number, data: CompleteTaskData): Promise<TaskCompletion> =>
    api.post(`/user/${taskId}/complete`, data).then(r => r.data),

  cancelTask: (taskId: number): Promise<void> =>
    api.post(`/user/${taskId}/cancel`).then(r => r.data),

  // Dashboard
  getDashboard: (): Promise<UserDashboard> =>
    api.get('/user/dashboard').then(r => r.data),

  // Notifications
  getNotifications: (): Promise<Notification[]> =>
    api.get('/user/notifications').then(r => r.data),

  markNotificationRead: (id: number): Promise<void> =>
    api.post(`/user/notifications/${id}/read`).then(r => r.data),

  markAllNotificationsRead: (): Promise<void> =>
    api.post('/user/notifications/mark-all-read').then(r => r.data),
};
