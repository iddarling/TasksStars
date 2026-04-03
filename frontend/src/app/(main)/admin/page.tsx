'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useUserStore } from '@/store/userStore';
import { useAppStore } from '@/store/appStore';
import { adminApi } from '@/services/adminApi';
import { Task, TaskCompletion, Reward, RewardRequest, AdminDashboardStats, PendingTask } from '@/types';
import { 
  Shield, Users, CheckCircle, XCircle, Clock, Star, 
  Target, Gift, TrendingUp, Loader2, CheckSquare, ArrowRight
} from 'lucide-react';

interface AdminUser {
  id: number;
  email: string;
  role: string;
  balance: number;
}

export default function AdminPage() {
  const router = useRouter();
  const { user } = useUserStore();
  const { wsClient } = useAppStore();
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'tasks' | 'completions' | 'rewards'>('overview');
  const [stats, setStats] = useState<AdminDashboardStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [pendingTasks, setPendingTasks] = useState<PendingTask[]>([]);
  const [pendingCompletions, setPendingCompletions] = useState<TaskCompletion[]>([]);
  const [pendingRewards, setPendingRewards] = useState<Reward[]>([]);
  const [rewardRequests, setRewardRequests] = useState<RewardRequest[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [moderationComment, setModerationComment] = useState('');

  useEffect(() => {
    if (user?.role !== 'ADMIN') {
      router.push('/dashboard');
      return;
    }
    loadAllData();
  }, [user, router]);

  // WebSocket listener for real-time updates
  useEffect(() => {
    if (!wsClient || user?.role !== 'ADMIN') return;

    const handleMessage = (message: { type: string; data?: any }) => {
      switch (message.type) {
        case 'task_suggested_by_user':
          console.log('New task suggested, refreshing pending tasks...');
          loadPendingTasks();
          break;
        case 'task_completion_pending_review':
          console.log('New task completion pending, refreshing completions...');
          loadPendingCompletions();
          break;
        case 'reward_suggested_by_user':
          console.log('New reward suggested, refreshing pending rewards...');
          loadPendingRewards();
          break;
        case 'reward_redemption_requested':
          console.log('New reward redemption requested, refreshing requests...');
          loadRewardRequests();
          break;
      }
    };

    wsClient.on('task_suggested_by_user', handleMessage);
    wsClient.on('task_completion_pending_review', handleMessage);
    wsClient.on('reward_suggested_by_user', handleMessage);
    wsClient.on('reward_redemption_requested', handleMessage);
    
    return () => {
      wsClient.off('task_suggested_by_user', handleMessage);
      wsClient.off('task_completion_pending_review', handleMessage);
      wsClient.off('reward_suggested_by_user', handleMessage);
      wsClient.off('reward_redemption_requested', handleMessage);
    };
  }, [wsClient, user?.role]);

  const loadPendingTasks = async () => {
    try {
      const tasks = await adminApi.getPendingTasks();
      setPendingTasks(tasks);
    } catch (error) {
      console.error('Failed to load pending tasks', error);
    }
  };

  const loadPendingCompletions = async () => {
    try {
      const completions = await adminApi.getPendingCompletions();
      setPendingCompletions(completions);
    } catch (error) {
      console.error('Failed to load pending completions', error);
    }
  };

  const loadPendingRewards = async () => {
    try {
      const rewards = await adminApi.getPendingRewards();
      setPendingRewards(rewards);
    } catch (error) {
      console.error('Failed to load pending rewards', error);
    }
  };

  const loadRewardRequests = async () => {
    try {
      const requests = await adminApi.getRewardRequests('pending');
      setRewardRequests(requests);
    } catch (error) {
      console.error('Failed to load reward requests', error);
    }
  };

  const loadAllData = async () => {
    setIsLoading(true);
    try {
      const [statsData, usersData, tasks, completions, rewards, requests] = await Promise.all([
        adminApi.getDashboardStats(),
        adminApi.getUsers(),
        adminApi.getPendingTasks(),
        adminApi.getPendingCompletions(),
        adminApi.getPendingRewards(),
        adminApi.getRewardRequests('pending'),
      ]);
      setStats(statsData);
      setUsers(usersData);
      setPendingTasks(tasks);
      setPendingCompletions(completions);
      setPendingRewards(rewards);
      setRewardRequests(requests);
    } catch (error) {
      console.error('Failed to load admin data', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApproveTask = async (taskId: number) => {
    try {
      await adminApi.approveTaskSuggestion(taskId, { comment: moderationComment });
      setPendingTasks(pendingTasks.filter(t => t.id !== taskId));
      setModerationComment('');
    } catch (error) {
      console.error('Failed to approve task', error);
    }
  };

  const handleRejectTask = async (taskId: number) => {
    try {
      await adminApi.rejectTaskSuggestion(taskId, { comment: moderationComment });
      setPendingTasks(pendingTasks.filter(t => t.id !== taskId));
      setModerationComment('');
    } catch (error) {
      console.error('Failed to reject task', error);
    }
  };

  const handleApproveCompletion = async (completionId: number) => {
    try {
      await adminApi.approveCompletion(completionId, { comment: moderationComment });
      setPendingCompletions(pendingCompletions.filter(c => c.id !== completionId));
      setModerationComment('');
    } catch (error) {
      console.error('Failed to approve completion', error);
    }
  };

  const handleRejectCompletion = async (completionId: number) => {
    try {
      await adminApi.rejectCompletion(completionId, { comment: moderationComment });
      setPendingCompletions(pendingCompletions.filter(c => c.id !== completionId));
      setModerationComment('');
    } catch (error) {
      console.error('Failed to reject completion', error);
    }
  };

  const handleApproveReward = async (rewardId: number) => {
    try {
      await adminApi.approveReward(rewardId);
      setPendingRewards(pendingRewards.filter(r => r.id !== rewardId));
    } catch (error) {
      console.error('Failed to approve reward', error);
    }
  };

  const handleRejectReward = async (rewardId: number) => {
    try {
      await adminApi.rejectReward(rewardId);
      setPendingRewards(pendingRewards.filter(r => r.id !== rewardId));
    } catch (error) {
      console.error('Failed to reject reward', error);
    }
  };

  const handleApproveRewardRequest = async (requestId: number) => {
    try {
      await adminApi.approveRewardRequest(requestId, { comment: moderationComment });
      setRewardRequests(rewardRequests.filter(r => r.id !== requestId));
      setModerationComment('');
    } catch (error) {
      console.error('Failed to approve reward request', error);
    }
  };

  const handleRejectRewardRequest = async (requestId: number) => {
    try {
      await adminApi.rejectRewardRequest(requestId, { comment: moderationComment });
      setRewardRequests(rewardRequests.filter(r => r.id !== requestId));
      setModerationComment('');
    } catch (error) {
      console.error('Failed to reject reward request', error);
    }
  };

  if (user?.role !== 'ADMIN') return null;

  return (
    <div className="p-4 space-y-6 animate-in fade-in duration-500 pb-24">
      <header className="flex justify-between items-center py-2">
        <div className="flex items-center gap-3">
          <div className="bg-yellow-500 p-2 rounded-xl">
            <Shield size={24} className="text-black" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-white uppercase italic">ADMIN</h1>
            <p className="text-zinc-500 text-[10px] font-black uppercase tracking-[0.2em]">CONTROL CENTER</p>
          </div>
        </div>
      </header>

      {/* TABS */}
      <div className="flex gap-2 overflow-x-auto scrollbar-hide">
        {(['overview', 'users', 'tasks', 'completions', 'rewards'] as const).map((tab) => {
          const counts = {
            overview: 0,
            users: users.length,
            tasks: pendingTasks.length,
            completions: pendingCompletions.length,
            rewards: pendingRewards.length + rewardRequests.length,
          };
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex items-center gap-2 px-4 py-3 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all border whitespace-nowrap ${
                activeTab === tab
                  ? 'bg-yellow-500 text-black border-yellow-500'
                  : 'bg-zinc-900 text-zinc-500 border-zinc-800'
              }`}
            >
              {tab}
              {counts[tab] > 0 && (
                <span className="bg-red-500 text-white px-1.5 py-0.5 rounded-full text-[8px]">
                  {counts[tab]}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20 text-yellow-500">
          <Loader2 size={40} className="animate-spin" />
          <p className="mt-4 text-[10px] font-black uppercase tracking-widest italic">Loading...</p>
        </div>
      ) : (
        <>
          {/* OVERVIEW TAB */}
          {activeTab === 'overview' && stats && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2 text-zinc-500">
                    <Users size={16} />
                    <span className="text-[10px] font-black uppercase tracking-widest">Users</span>
                  </div>
                  <p className="text-2xl font-black text-white italic">{stats.users.total}</p>
                  <p className="text-[10px] text-zinc-600 mt-1">
                    {stats.users.admins} admins • {stats.users.regular} users
                  </p>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2 text-zinc-500">
                    <Target size={16} />
                    <span className="text-[10px] font-black uppercase tracking-widest">Tasks</span>
                  </div>
                  <p className="text-2xl font-black text-white italic">{stats.tasks.total}</p>
                  <p className="text-[10px] text-zinc-600 mt-1">
                    {stats.tasks.active} active • {stats.tasks.draft} draft
                  </p>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2 text-zinc-500">
                    <CheckSquare size={16} />
                    <span className="text-[10px] font-black uppercase tracking-widest">Completions</span>
                  </div>
                  <p className="text-2xl font-black text-white italic">{stats.completions.total}</p>
                  <p className="text-[10px] text-zinc-600 mt-1">
                    {stats.completions.pending} pending • {stats.completions.approved} approved
                  </p>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2 text-zinc-500">
                    <Star size={16} />
                    <span className="text-[10px] font-black uppercase tracking-widest">Points</span>
                  </div>
                  <p className="text-2xl font-black text-white italic">{stats.points.total_awarded}</p>
                  <p className="text-[10px] text-zinc-600 mt-1">
                    {stats.points.total_redeemed} redeemed
                  </p>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
                <h3 className="text-yellow-500 font-bold text-sm mb-3">Pending Moderation</h3>
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-zinc-400">Task Suggestions</span>
                    <span className="text-white font-bold">{pendingTasks.length}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-zinc-400">Task Completions</span>
                    <span className="text-white font-bold">{pendingCompletions.length}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-zinc-400">Reward Requests</span>
                    <span className="text-white font-bold">{rewardRequests.length}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* USERS TAB */}
          {activeTab === 'users' && (
            <div className="space-y-4">
              {users.length === 0 ? (
                <div className="text-center py-20 border-2 border-dashed border-zinc-900 rounded-3xl">
                  <Users className="mx-auto text-zinc-600 mb-4" size={40} />
                  <p className="text-zinc-500 text-xs font-black uppercase tracking-widest">NO USERS</p>
                </div>
              ) : (
                users.map(u => (
                  <div key={u.id} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-zinc-800 rounded-full flex items-center justify-center">
                        <span className="text-white font-black text-lg">{u.email[0].toUpperCase()}</span>
                      </div>
                      <div>
                        <h3 className="font-bold text-white">{u.email}</h3>
                        <p className="text-zinc-500 text-[10px] uppercase">
                          {u.role} • {u.balance} stars
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => router.push(`/admin/users/${u.id}`)}
                      className="p-3 bg-yellow-500/10 text-yellow-500 rounded-xl hover:bg-yellow-500/20 transition-colors"
                    >
                      <ArrowRight size={20} />
                    </button>
                  </div>
                ))
              )}
            </div>
          )}

          {/* PENDING TASKS TAB */}
          {activeTab === 'tasks' && (
            <div className="space-y-4">
              {pendingTasks.length === 0 ? (
                <div className="text-center py-20 border-2 border-dashed border-zinc-900 rounded-3xl">
                  <CheckCircle className="mx-auto text-zinc-600 mb-4" size={40} />
                  <p className="text-zinc-500 text-xs font-black uppercase tracking-widest">NO PENDING TASKS</p>
                </div>
              ) : (
                pendingTasks.map(task => (
                  <div key={task.id} className="bg-zinc-900 border border-blue-500/30 rounded-xl p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-bold text-white">{task.title}</h3>
                        <p className="text-zinc-400 text-sm mt-1">{task.description}</p>
                      </div>
                      <span className="text-[10px] uppercase bg-blue-500/20 text-blue-400 px-2 py-1 rounded">
                        pending approval
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-[10px] text-zinc-500 mb-4">
                      <span className="flex items-center gap-1">
                        <Star size={12} className="text-yellow-500" />
                        {task.points} stars
                      </span>
                      <span className="uppercase">{task.type}</span>
                      {task.suggested_by && (
                        <span>By {task.suggested_by.email || `user #${task.suggested_by.id}`}</span>
                      )}
                    </div>
                    <textarea
                      placeholder="Add moderation comment (optional)..."
                      value={moderationComment}
                      onChange={(e) => setModerationComment(e.target.value)}
                      className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white text-sm mb-3 focus:outline-none focus:border-yellow-500"
                      rows={2}
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleApproveTask(task.id)}
                        className="flex-1 bg-green-500 text-black font-bold py-2 rounded-lg hover:bg-green-400 transition-colors flex items-center justify-center gap-2"
                      >
                        <CheckCircle size={16} />
                        APPROVE
                      </button>
                      <button
                        onClick={() => handleRejectTask(task.id)}
                        className="flex-1 bg-red-500/20 text-red-500 font-bold py-2 rounded-lg hover:bg-red-500/30 transition-colors flex items-center justify-center gap-2"
                      >
                        <XCircle size={16} />
                        REJECT
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* PENDING COMPLETIONS TAB */}
          {activeTab === 'completions' && (
            <div className="space-y-4">
              {pendingCompletions.length === 0 ? (
                <div className="text-center py-20 border-2 border-dashed border-zinc-900 rounded-3xl">
                  <CheckCircle className="mx-auto text-zinc-600 mb-4" size={40} />
                  <p className="text-zinc-500 text-xs font-black uppercase tracking-widest">NO PENDING COMPLETIONS</p>
                </div>
              ) : (
                pendingCompletions.map(completion => (
                  <div key={completion.id} className="bg-zinc-900 border border-yellow-500/30 rounded-xl p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-bold text-white">{completion.task?.title}</h3>
                        <p className="text-zinc-400 text-sm mt-1">{completion.task?.description}</p>
                      </div>
                      <span className="text-[10px] uppercase bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded">
                        awaiting review
                      </span>
                    </div>
                    <div className="bg-zinc-950 rounded-lg p-3 mb-4">
                      <p className="text-[10px] text-zinc-500 uppercase mb-1">Proof submitted:</p>
                      <p className="text-white text-sm">{completion.proof}</p>
                    </div>
                    <div className="flex items-center gap-4 text-[10px] text-zinc-500 mb-4">
                      <span className="flex items-center gap-1">
                        <Star size={12} className="text-yellow-500" />
                        {completion.task?.points} stars reward
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock size={12} />
                        {Math.floor((completion.time_spent || 0) / 60)}m spent
                      </span>
                    </div>
                    <textarea
                      placeholder="Add review comment (optional)..."
                      value={moderationComment}
                      onChange={(e) => setModerationComment(e.target.value)}
                      className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white text-sm mb-3 focus:outline-none focus:border-yellow-500"
                      rows={2}
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleApproveCompletion(completion.id)}
                        className="flex-1 bg-green-500 text-black font-bold py-2 rounded-lg hover:bg-green-400 transition-colors flex items-center justify-center gap-2"
                      >
                        <CheckCircle size={16} />
                        APPROVE & AWARD
                      </button>
                      <button
                        onClick={() => handleRejectCompletion(completion.id)}
                        className="flex-1 bg-red-500/20 text-red-500 font-bold py-2 rounded-lg hover:bg-red-500/30 transition-colors flex items-center justify-center gap-2"
                      >
                        <XCircle size={16} />
                        REJECT
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* REWARDS TAB */}
          {activeTab === 'rewards' && (
            <div className="space-y-6">
              {/* Proposed Rewards */}
              <section>
                <h3 className="text-sm font-black text-zinc-500 uppercase tracking-widest mb-3">
                  Proposed Rewards ({pendingRewards.length})
                </h3>
                {pendingRewards.length === 0 ? (
                  <p className="text-zinc-600 text-[10px]">No proposed rewards</p>
                ) : (
                  <div className="space-y-3">
                    {pendingRewards.map(reward => (
                      <div key={reward.id} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-bold text-white">{reward.title}</h4>
                            <p className="text-zinc-400 text-sm">{reward.description}</p>
                          </div>
                          <span className="text-yellow-500 font-bold">{reward.cost}★</span>
                        </div>
                        <div className="flex gap-2 mt-3">
                          <button
                            onClick={() => handleApproveReward(reward.id)}
                            className="flex-1 bg-green-500 text-black font-bold py-2 rounded-lg hover:bg-green-400 transition-colors text-sm"
                          >
                            APPROVE
                          </button>
                          <button
                            onClick={() => handleRejectReward(reward.id)}
                            className="flex-1 bg-red-500/20 text-red-500 font-bold py-2 rounded-lg hover:bg-red-500/30 transition-colors text-sm"
                          >
                            REJECT
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              {/* Reward Redemption Requests */}
              <section>
                <h3 className="text-sm font-black text-zinc-500 uppercase tracking-widest mb-3">
                  Redemption Requests ({rewardRequests.length})
                </h3>
                {rewardRequests.length === 0 ? (
                  <p className="text-zinc-600 text-[10px]">No pending requests</p>
                ) : (
                  <div className="space-y-3">
                    {rewardRequests.map(request => (
                      <div key={request.id} className="bg-zinc-900 border border-purple-500/30 rounded-xl p-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-bold text-white">{request.reward?.title}</h4>
                            <p className="text-zinc-400 text-sm">Requested by user #{request.user_id}</p>
                          </div>
                          <span className="text-yellow-500 font-bold">{request.reward?.cost}★</span>
                        </div>
                        <textarea
                          placeholder="Add comment (optional)..."
                          value={moderationComment}
                          onChange={(e) => setModerationComment(e.target.value)}
                          className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white text-sm mt-3 mb-3 focus:outline-none focus:border-yellow-500"
                          rows={2}
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleApproveRewardRequest(request.id)}
                            className="flex-1 bg-green-500 text-black font-bold py-2 rounded-lg hover:bg-green-400 transition-colors text-sm"
                          >
                            APPROVE
                          </button>
                          <button
                            onClick={() => handleRejectRewardRequest(request.id)}
                            className="flex-1 bg-red-500/20 text-red-500 font-bold py-2 rounded-lg hover:bg-red-500/30 transition-colors text-sm"
                          >
                            REJECT
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </div>
          )}
        </>
      )}
    </div>
  );
}
