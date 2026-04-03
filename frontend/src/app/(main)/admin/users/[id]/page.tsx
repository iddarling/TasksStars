'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useUserStore } from '@/store/userStore';
import { adminApi } from '@/services/adminApi';
import { 
  ArrowLeft, User, Star, Clock, CheckCircle, Gift, 
  TrendingUp, AlertCircle, Plus, Minus, Loader2 
} from 'lucide-react';

interface UserDetails {
  user: {
    id: number;
    email: string;
    role: string;
    created_at: string;
    balance: number;
  };
  active_tasks: Array<{
    id: number;
    task_id: number;
    title: string;
    description: string;
    points: number;
    started_at: string;
    time_spent: number;
  }>;
  completed_tasks: Array<{
    id: number;
    task_id: number;
    title: string;
    points_awarded: number;
    completed_at: string;
    time_spent: number;
  }>;
  pending_completions: Array<{
    id: number;
    task_id: number;
    title: string;
    proof: string;
    proof_image_url: string;
    points: number;
    created_at: string;
  }>;
  reward_requests: Array<{
    id: number;
    reward_id: number;
    reward_title: string;
    reward_description: string;
    points_spent: number;
    status: string;
    created_at: string;
  }>;
  points_history: Array<{
    id: number;
    amount: number;
    source: string;
    created_at: string;
  }>;
}

export default function AdminUserDetailPage() {
  const router = useRouter();
  const params = useParams();
  const { user } = useUserStore();
  const [userData, setUserData] = useState<UserDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'tasks' | 'rewards' | 'history'>('overview');
  const [adjustAmount, setAdjustAmount] = useState('');
  const [adjustReason, setAdjustReason] = useState('');
  const [isAdjusting, setIsAdjusting] = useState(false);
  const [error, setError] = useState('');

  const userId = parseInt(params.id as string);

  useEffect(() => {
    if (user?.role !== 'ADMIN') {
      router.push('/dashboard');
      return;
    }
    loadUserData();
  }, [user, router, userId]);

  const loadUserData = async () => {
    try {
      setIsLoading(true);
      const data = await adminApi.getUserDetails(userId);
      setUserData(data);
    } catch (error) {
      console.error('Failed to load user details', error);
      setError('Failed to load user details');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAdjustBalance = async (isAdd: boolean) => {
    const amount = parseInt(adjustAmount);
    if (!amount || !adjustReason.trim()) {
      setError('Please enter amount and reason');
      return;
    }

    try {
      setIsAdjusting(true);
      setError('');
      await adminApi.adjustPoints({
        user_id: userId,
        amount: isAdd ? amount : -amount,
        reason: adjustReason
      });
      setAdjustAmount('');
      setAdjustReason('');
      await loadUserData();
    } catch (error) {
      console.error('Failed to adjust balance', error);
      setError('Failed to adjust balance');
    } finally {
      setIsAdjusting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <Loader2 size={40} className="animate-spin text-yellow-500 mx-auto mb-4" />
          <p className="text-zinc-500 text-sm uppercase tracking-widest">Loading User...</p>
        </div>
      </div>
    );
  }

  if (!userData) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <AlertCircle size={40} className="text-red-500 mx-auto mb-4" />
          <p className="text-zinc-500 text-sm uppercase tracking-widest">User not found</p>
        </div>
      </div>
    );
  }

  const { user: userInfo, active_tasks, completed_tasks, pending_completions, reward_requests, points_history } = userData;

  return (
    <div className="min-h-screen bg-black p-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <button 
          onClick={() => router.push('/admin')}
          className="p-3 bg-zinc-900 rounded-xl hover:bg-zinc-800 transition-colors"
        >
          <ArrowLeft size={20} className="text-zinc-400" />
        </button>
        <div>
          <h1 className="text-2xl font-black text-white uppercase italic tracking-tight">User Management</h1>
          <p className="text-zinc-500 text-xs uppercase tracking-widest">{userInfo.email}</p>
        </div>
        <div className="ml-auto flex items-center gap-2 bg-zinc-900 px-4 py-2 rounded-xl">
          <Star size={16} className="text-yellow-500 fill-yellow-500" />
          <span className="text-white font-bold">{userInfo.balance}</span>
          <span className="text-zinc-500 text-xs uppercase">stars</span>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-center gap-3">
          <AlertCircle size={20} className="text-red-500" />
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* Balance Adjustment Card - Redesigned */}
      <div className="mb-8 bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-black text-white uppercase italic flex items-center gap-2">
            <TrendingUp size={20} className="text-yellow-500" />
            Balance Adjustment
          </h2>
          <div className="flex items-center gap-2 bg-black px-4 py-2 rounded-xl border border-zinc-800">
            <Star size={16} className="text-yellow-500 fill-yellow-500" />
            <span className="text-white font-bold">{userInfo.balance}</span>
            <span className="text-zinc-500 text-xs uppercase">current</span>
          </div>
        </div>

        {/* Quick Amount Buttons */}
        <div className="mb-4">
          <label className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider block mb-3">
            Quick Select Amount
          </label>
          <div className="flex gap-2 flex-wrap">
            {[10, 50, 100, 500, 1000].map((amount) => (
              <button
                key={amount}
                onClick={() => setAdjustAmount(amount.toString())}
                className={`px-4 py-2 rounded-xl font-bold text-sm transition-all border ${
                  adjustAmount === amount.toString()
                    ? 'bg-yellow-500 text-black border-yellow-500'
                    : 'bg-zinc-800 text-zinc-400 border-zinc-700 hover:bg-zinc-700 hover:text-white'
                }`}
              >
                {amount}★
              </button>
            ))}
          </div>
        </div>

        {/* Custom Amount Input */}
        <div className="mb-4">
          <label className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider block mb-2">
            Or Enter Custom Amount
          </label>
          <div className="relative">
            <input 
              type="number"
              value={adjustAmount}
              onChange={(e) => setAdjustAmount(e.target.value)}
              className="w-full bg-black border border-zinc-800 rounded-xl p-4 pl-12 text-white font-bold text-lg focus:border-yellow-500 transition-colors focus:outline-none"
              placeholder="0"
              min="1"
            />
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-yellow-500 font-bold text-lg">★</span>
          </div>
        </div>

        {/* Reason Input */}
        <div className="mb-6">
          <label className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider block mb-2">
            Reason for Adjustment
          </label>
          <input 
            type="text"
            value={adjustReason}
            onChange={(e) => setAdjustReason(e.target.value)}
            className="w-full bg-black border border-zinc-800 rounded-xl p-4 text-white font-bold focus:border-yellow-500 transition-colors focus:outline-none"
            placeholder="e.g. Bonus for completing special task, Correction, etc."
          />
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-4">
          <button 
            onClick={() => handleAdjustBalance(true)}
            disabled={isAdjusting || !adjustAmount || !adjustReason.trim()}
            className="py-4 bg-green-500 text-black font-black uppercase text-sm tracking-widest rounded-xl hover:bg-green-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isAdjusting ? (
              <Loader2 size={20} className="animate-spin" />
            ) : (
              <>
                <Plus size={20} />
                ADD STARS
              </>
            )}
          </button>
          <button 
            onClick={() => handleAdjustBalance(false)}
            disabled={isAdjusting || !adjustAmount || !adjustReason.trim()}
            className="py-4 bg-red-500 text-black font-black uppercase text-sm tracking-widest rounded-xl hover:bg-red-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isAdjusting ? (
              <Loader2 size={20} className="animate-spin" />
            ) : (
              <>
                <Minus size={20} />
                DEDUCT STARS
              </>
            )}
          </button>
        </div>

        {/* Helper Text */}
        <p className="text-zinc-600 text-[10px] text-center mt-4 uppercase tracking-wider">
          Select amount or enter custom, add reason, then click Add or Deduct
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {(['overview', 'tasks', 'rewards', 'history'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-6 py-3 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all border ${
              activeTab === tab 
                ? 'bg-yellow-500 text-black border-yellow-500' 
                : 'bg-zinc-900 text-zinc-500 border-zinc-800'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2 text-zinc-500">
              <Clock size={16} />
              <span className="text-[10px] font-black uppercase tracking-widest">Active Tasks</span>
            </div>
            <p className="text-3xl font-black text-white italic">{active_tasks.length}</p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2 text-zinc-500">
              <CheckCircle size={16} />
              <span className="text-[10px] font-black uppercase tracking-widest">Completed</span>
            </div>
            <p className="text-3xl font-black text-white italic">{completed_tasks.length}</p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2 text-zinc-500">
              <Gift size={16} />
              <span className="text-[10px] font-black uppercase tracking-widest">Reward Requests</span>
            </div>
            <p className="text-3xl font-black text-white italic">{reward_requests.length}</p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2 text-zinc-500">
              <Star size={16} />
              <span className="text-[10px] font-black uppercase tracking-widest">Current Balance</span>
            </div>
            <p className="text-3xl font-black text-yellow-500 italic">{userInfo.balance}</p>
          </div>
        </div>
      )}

      {/* Tasks Tab */}
      {activeTab === 'tasks' && (
        <div className="space-y-6">
          {/* Active Tasks */}
          <div>
            <h3 className="text-sm font-black text-yellow-500 uppercase tracking-widest mb-3 flex items-center gap-2">
              <Clock size={16} />
              Active Tasks ({active_tasks.length})
            </h3>
            {active_tasks.length > 0 ? (
              <div className="space-y-2">
                {active_tasks.map((task) => (
                  <div key={task.id} className="bg-zinc-900 border border-yellow-500/30 rounded-xl p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-bold text-white">{task.title}</h4>
                        <p className="text-zinc-400 text-sm mt-1">{task.description}</p>
                      </div>
                      <span className="text-yellow-500 font-bold">+{task.points}★</span>
                    </div>
                    <p className="text-zinc-500 text-[10px] mt-2">
                      Started: {new Date(task.started_at).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-zinc-500 text-sm">No active tasks</p>
            )}
          </div>

          {/* Pending Completions */}
          <div>
            <h3 className="text-sm font-black text-blue-500 uppercase tracking-widest mb-3 flex items-center gap-2">
              <AlertCircle size={16} />
              Pending Review ({pending_completions.length})
            </h3>
            {pending_completions.length > 0 ? (
              <div className="space-y-2">
                {pending_completions.map((task) => (
                  <div key={task.id} className="bg-zinc-900 border border-blue-500/30 rounded-xl p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-bold text-white">{task.title}</h4>
                        <p className="text-zinc-400 text-sm mt-1">{task.proof}</p>
                      </div>
                      <span className="text-blue-500 font-bold">+{task.points}★</span>
                    </div>
                    {task.proof_image_url && (
                      <img 
                        src={task.proof_image_url} 
                        alt="Proof" 
                        className="mt-2 rounded-lg max-h-32 object-cover"
                      />
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-zinc-500 text-sm">No pending completions</p>
            )}
          </div>

          {/* Completed Tasks */}
          <div>
            <h3 className="text-sm font-black text-green-500 uppercase tracking-widest mb-3 flex items-center gap-2">
              <CheckCircle size={16} />
              Completed ({completed_tasks.length})
            </h3>
            {completed_tasks.length > 0 ? (
              <div className="space-y-2">
                {completed_tasks.map((task) => (
                  <div key={task.id} className="bg-zinc-900/50 border border-green-500/30 rounded-xl p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-bold text-white">{task.title}</h4>
                        <p className="text-zinc-500 text-[10px] mt-1">
                          Completed: {new Date(task.completed_at).toLocaleDateString()}
                        </p>
                      </div>
                      <span className="text-green-500 font-bold">+{task.points_awarded}★</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-zinc-500 text-sm">No completed tasks</p>
            )}
          </div>
        </div>
      )}

      {/* Rewards Tab */}
      {activeTab === 'rewards' && (
        <div>
          <h3 className="text-sm font-black text-yellow-500 uppercase tracking-widest mb-3 flex items-center gap-2">
            <Gift size={16} />
            Reward Requests ({reward_requests.length})
          </h3>
          {reward_requests.length > 0 ? (
            <div className="space-y-2">
              {reward_requests.map((request) => (
                <div 
                  key={request.id} 
                  className={`bg-zinc-900 border rounded-xl p-4 ${
                    request.status === 'pending' ? 'border-blue-500/30' : 
                    request.status === 'approved' ? 'border-green-500/30' : 'border-red-500/30'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-bold text-white">{request.reward_title}</h4>
                      <p className="text-zinc-400 text-sm mt-1">{request.reward_description}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-yellow-500 font-bold block">-{request.points_spent}★</span>
                      <span className={`text-[10px] uppercase font-bold ${
                        request.status === 'pending' ? 'text-blue-500' : 
                        request.status === 'approved' ? 'text-green-500' : 'text-red-500'
                      }`}>
                        {request.status}
                      </span>
                    </div>
                  </div>
                  <p className="text-zinc-500 text-[10px] mt-2">
                    Requested: {new Date(request.created_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-zinc-500 text-sm">No reward requests</p>
          )}
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div>
          <h3 className="text-sm font-black text-yellow-500 uppercase tracking-widest mb-3 flex items-center gap-2">
            <TrendingUp size={16} />
            Points History ({points_history.length})
          </h3>
          {points_history.length > 0 ? (
            <div className="space-y-2">
              {points_history.map((record) => (
                <div key={record.id} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex justify-between items-center">
                  <div>
                    <p className="text-white font-medium">{record.source}</p>
                    <p className="text-zinc-500 text-[10px]">
                      {new Date(record.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span className={`font-bold ${record.amount > 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {record.amount > 0 ? '+' : ''}{record.amount}★
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-zinc-500 text-sm">No points history</p>
          )}
        </div>
      )}
    </div>
  );
}
