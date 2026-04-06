import { create } from 'zustand';
import { Task, Reward, TaskCompletion, Notification, UserDashboard } from '../types';
import { userTasksApi } from '../services/userTasksApi';
import { userRewardsApi } from '../services/userRewardsApi';
import api from '../services/api';
import { WebSocketClient, WebSocketMessage } from '../services/websocket';

interface AppState {
  // Tasks
  tasks: Task[];
  activeCompletions: TaskCompletion[];
  pendingTasks: Task[];
  completedTasks: TaskCompletion[];
  awaitingReviewTasks: TaskCompletion[];
  
  // Rewards
  rewards: Reward[];
  myRewardRequests: any[];
  
  // User data
  balance: number;
  dashboard: UserDashboard | null;
  notifications: Notification[];
  unreadNotificationsCount: number;
  
  // Loading states
  isLoading: boolean;
  activeTaskTimers: Record<number, { startTime: number; taskId: number }>;
  
  // WebSocket
  wsClient: WebSocketClient | null;
  
  // Actions - WebSocket
  initWebSocket: (token: string) => void;
  disconnectWebSocket: () => void;
  handleWebSocketMessage: (message: WebSocketMessage) => void;
  
  // Actions - Tasks
  fetchTasks: () => Promise<void>;
  suggestTask: (data: Parameters<typeof userTasksApi.suggestTask>[0]) => Promise<void>;
  startTask: (taskId: number) => Promise<TaskCompletion>;
  completeTask: (taskId: number, data: { proof: string; proof_image_url?: string }) => Promise<TaskCompletion>;
  cancelTask: (taskId: number) => Promise<void>;
  fetchMyActiveTasks: () => Promise<void>;
  fetchMyPendingTasks: () => Promise<void>;
  fetchMyCompletedTasks: () => Promise<void>;
  fetchMyAwaitingReviewTasks: () => Promise<void>;
  
  // Actions - Rewards
  fetchRewards: () => Promise<void>;
  suggestReward: (data: Parameters<typeof userRewardsApi.suggestReward>[0]) => Promise<void>;
  redeemReward: (rewardId: number) => Promise<void>;
  fetchMyRewardRequests: () => Promise<void>;
  
  // Actions - Dashboard & Data
  fetchBalance: () => Promise<void>;
  fetchDashboard: () => Promise<void>;
  fetchNotifications: () => Promise<void>;
  markNotificationRead: (id: number) => Promise<void>;
  markAllNotificationsRead: () => Promise<void>;
  
  // Timer management
  getElapsedTime: (completionId: number) => number;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  tasks: [],
  activeCompletions: [],
  pendingTasks: [],
  completedTasks: [],
  awaitingReviewTasks: [],
  rewards: [],
  myRewardRequests: [],
  balance: 0,
  dashboard: null,
  notifications: [],
  unreadNotificationsCount: 0,
  isLoading: false,
  activeTaskTimers: {},
  wsClient: null,

  // Initialize WebSocket connection
  initWebSocket: (token: string) => {
    const ws = new WebSocketClient(token);
    ws.connect();
    
    // Subscribe to all events
    ws.on('*', (message) => {
      get().handleWebSocketMessage(message);
    });
    
    set({ wsClient: ws });
  },

  // Disconnect WebSocket
  disconnectWebSocket: () => {
    const ws = get().wsClient;
    if (ws) {
      ws.disconnect();
      set({ wsClient: null });
    }
  },

  // Handle WebSocket messages
  handleWebSocketMessage: (message: WebSocketMessage) => {
    console.log('WebSocket message received:', message);
    
    switch (message.type) {
      // Task events
      case 'task_started':
        get().fetchMyActiveTasks();
        get().fetchTasks();
        break;
        
      case 'task_completed_pending':
      case 'task_completed_approved':
        get().fetchMyActiveTasks();
        get().fetchMyCompletedTasks();
        get().fetchTasks();
        get().fetchBalance();
        get().fetchNotifications();
        break;

      case 'task_assigned':
        get().fetchTasks();
        get().fetchNotifications();
        break;
        
      case 'task_cancelled':
        get().fetchMyActiveTasks();
        get().fetchTasks();
        break;
        
      // Task suggestion events
      case 'task_suggestion_approved':
        get().fetchMyPendingTasks();
        get().fetchTasks();
        get().fetchNotifications();
        break;
        
      case 'task_suggestion_rejected':
        get().fetchMyPendingTasks();
        get().fetchNotifications();
        break;
        
      // Completion approval events (from admin)
      case 'completion_approved':
        get().fetchMyActiveTasks();
        get().fetchMyCompletedTasks();
        get().fetchMyAwaitingReviewTasks();
        get().fetchBalance();
        get().fetchNotifications();
        break;
        
      case 'completion_rejected':
        get().fetchMyActiveTasks();
        get().fetchNotifications();
        break;
        
      // Reward events
      case 'reward_suggested':
        get().fetchMyRewardRequests();
        break;
        
      case 'reward_redeemed':
        get().fetchMyRewardRequests();
        get().fetchRewards();
        break;
        
      case 'reward_request_approved':
        get().fetchMyRewardRequests();
        get().fetchBalance();
        get().fetchNotifications();
        break;
        
      case 'reward_request_rejected':
        get().fetchMyRewardRequests();
        get().fetchNotifications();
        break;
        
      // Connection events
      case 'connected':
        console.log('WebSocket connected successfully');
        // Refresh all data on connection
        get().fetchTasks();
        get().fetchMyActiveTasks();
        get().fetchMyPendingTasks();
        get().fetchRewards();
        get().fetchMyRewardRequests();
        get().fetchBalance();
        get().fetchNotifications();
        break;
        
      default:
        console.log('Unknown WebSocket message type:', message.type);
    }
  },

  // Fetch all active tasks
  fetchTasks: async () => {
    set({ isLoading: true });
    try {
      const response = await api.get('/tasks');
      set({ tasks: response.data });
    } catch (error) {
      console.error('Failed to fetch tasks', error);
    } finally {
      set({ isLoading: false });
    }
  },

  // Fetch available rewards
  fetchRewards: async () => {
    set({ isLoading: true });
    try {
      const data = await userRewardsApi.getAvailable();
      set({ rewards: data });
    } catch (error) {
      console.error('Failed to fetch rewards', error);
    } finally {
      set({ isLoading: false });
    }
  },

  // Fetch balance
  fetchBalance: async () => {
    try {
      const response = await api.get('/balance');
      set({ balance: response.data.balance });
    } catch (error) {
      console.error('Failed to fetch balance', error);
    }
  },

  // Suggest new task
  suggestTask: async (data) => {
    set({ isLoading: true });
    try {
      await userTasksApi.suggestTask(data);
      await get().fetchMyPendingTasks();
    } catch (error) {
      console.error('Failed to suggest task', error);
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  // Start task (timer)
  startTask: async (taskId) => {
    set({ isLoading: true });
    try {
      const completion = await userTasksApi.startTask(taskId);
      const timers = get().activeTaskTimers;
      timers[completion.id] = { startTime: Date.now(), taskId };
      set({ 
        activeTaskTimers: timers,
        activeCompletions: [...get().activeCompletions, completion]
      });
      return completion;
    } catch (error) {
      console.error('Failed to start task', error);
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  // Complete task with proof
  completeTask: async (taskId, data) => {
    set({ isLoading: true });
    try {
      // Get elapsed time from timer
      const completion = get().activeCompletions.find(c => c.task_id === taskId);
      const elapsedTime = completion ? get().getElapsedTime(completion.id) : 0;
      
      const completionResult = await userTasksApi.completeTask(taskId, {
        proof: data.proof,
        proof_image_url: data.proof_image_url,
        time_spent: elapsedTime
      });
      const timers = { ...get().activeTaskTimers };
      if (completion) {
        delete timers[completion.id];
      }
      set({ 
        activeTaskTimers: timers,
        activeCompletions: get().activeCompletions.filter(c => c.task_id !== taskId)
      });
      await get().fetchMyCompletedTasks();
      await get().fetchMyAwaitingReviewTasks();
      return completionResult;
    } catch (error) {
      console.error('Failed to complete task', error);
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  // Cancel task
  cancelTask: async (taskId) => {
    set({ isLoading: true });
    try {
      await userTasksApi.cancelTask(taskId);
      const timers = { ...get().activeTaskTimers };
      const completion = get().activeCompletions.find(c => c.task_id === taskId);
      if (completion) {
        delete timers[completion.id];
      }
      set({ 
        activeTaskTimers: timers,
        activeCompletions: get().activeCompletions.filter(c => c.task_id !== taskId)
      });
    } catch (error) {
      console.error('Failed to cancel task', error);
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  // Fetch user's active tasks (with timers)
  fetchMyActiveTasks: async () => {
    try {
      const data = await userTasksApi.getMyActive();
      set({ activeCompletions: data });
      
      // Initialize timers for each active task from started_at
      const timers: Record<number, { startTime: number; taskId: number }> = {};
      data.forEach((completion: any) => {
        if (completion.started_at) {
          // Ensure UTC by appending Z if not present
          const startedAtStr = completion.started_at.endsWith('Z') 
            ? completion.started_at 
            : completion.started_at + 'Z';
          timers[completion.id] = {
            startTime: new Date(startedAtStr).getTime(),
            taskId: completion.task_id
          };
        }
      });
      set({ activeTaskTimers: timers });
    } catch (error) {
      console.error('Failed to fetch active tasks', error);
    }
  },

  // Fetch user's pending tasks (awaiting approval)
  fetchMyPendingTasks: async () => {
    try {
      const data = await userTasksApi.getMyPending();
      set({ pendingTasks: data });
    } catch (error) {
      console.error('Failed to fetch pending tasks', error);
    }
  },

  // Fetch user's completed tasks history
  fetchMyCompletedTasks: async () => {
    try {
      const data = await userTasksApi.getMyCompleted();
      set({ completedTasks: data });
    } catch (error) {
      console.error('Failed to fetch completed tasks', error);
    }
  },

  // Fetch tasks awaiting review (completed but not yet approved)
  fetchMyAwaitingReviewTasks: async () => {
    try {
      const data = await userTasksApi.getMyAwaitingReview();
      set({ awaitingReviewTasks: data });
    } catch (error) {
      console.error('Failed to fetch awaiting review tasks', error);
    }
  },

  // Suggest reward
  suggestReward: async (data) => {
    set({ isLoading: true });
    try {
      await userRewardsApi.suggestReward(data);
      await get().fetchMyRewardRequests();
    } catch (error) {
      console.error('Failed to suggest reward', error);
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  // Redeem reward
  redeemReward: async (rewardId) => {
    set({ isLoading: true });
    try {
      await userRewardsApi.redeemReward(rewardId);
      await get().fetchBalance();
      await get().fetchMyRewardRequests();
    } catch (error) {
      console.error('Failed to redeem reward', error);
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  // Fetch my reward requests
  fetchMyRewardRequests: async () => {
    try {
      const data = await userRewardsApi.getMyRequests();
      set({ myRewardRequests: data });
    } catch (error) {
      console.error('Failed to fetch reward requests', error);
    }
  },

  // Fetch full dashboard
  fetchDashboard: async () => {
    set({ isLoading: true });
    try {
      const data = await userTasksApi.getDashboard();
      set({ 
        dashboard: data,
        balance: data.balance 
      });
    } catch (error) {
      console.error('Failed to fetch dashboard', error);
    } finally {
      set({ isLoading: false });
    }
  },

  // Fetch notifications
  fetchNotifications: async () => {
    try {
      const data = await userTasksApi.getNotifications();
      set({ 
        notifications: data,
        unreadNotificationsCount: data.filter(n => !n.is_read).length
      });
    } catch (error) {
      console.error('Failed to fetch notifications', error);
    }
  },

  // Mark notification as read
  markNotificationRead: async (id) => {
    try {
      await userTasksApi.markNotificationRead(id);
      const notifications = get().notifications.map(n => 
        n.id === id ? { ...n, is_read: true } : n
      );
      set({ 
        notifications,
        unreadNotificationsCount: notifications.filter(n => !n.is_read).length
      });
    } catch (error) {
      console.error('Failed to mark notification read', error);
    }
  },

  // Mark all notifications as read
  markAllNotificationsRead: async () => {
    try {
      await userTasksApi.markAllNotificationsRead();
      const notifications = get().notifications.map(n => ({ ...n, is_read: true }));
      set({ 
        notifications,
        unreadNotificationsCount: 0
      });
    } catch (error) {
      console.error('Failed to mark all notifications read', error);
    }
  },

  // Get elapsed time for active task
  getElapsedTime: (completionId) => {
    const timer = get().activeTaskTimers[completionId];
    if (!timer) return 0;
    return Math.floor((Date.now() - timer.startTime) / 1000);
  },
}));
