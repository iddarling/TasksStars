'use client';

import React, { useEffect, useState, useRef, memo } from 'react';
import { useAppStore } from '@/store/appStore';
import { useUserStore } from '@/store/userStore';
import { useRouter } from 'next/navigation';
import { AnimatedBalance } from '@/components/AnimatedBalance';
import { 
  Star, Trophy, TrendingUp, LogOut, Clock, CheckCircle, 
  Hourglass, Target, Zap, History
} from 'lucide-react';

// Memoized stat card to prevent re-renders
const StatCard = memo(({ icon: Icon, label, value, color = 'white' }: { 
  icon: React.ElementType; 
  label: string; 
  value: number | string;
  color?: string;
}) => (
  <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 min-h-[100px]">
    <div className="flex items-center gap-2 mb-2 text-zinc-500">
      <Icon size={16} />
      <span className="text-[10px] font-black uppercase tracking-widest">{label}</span>
    </div>
    <p className={`text-2xl font-black italic text-${color}`}>
      {value}
    </p>
  </div>
));
StatCard.displayName = 'StatCard';
const formatTime = (seconds: number) => {
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

// Component to show elapsed time for a task
const TaskTimer = ({ completionId, startedAt }: { completionId: number; startedAt: string }) => {
  const { getElapsedTime } = useAppStore();
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    // Initial calculation
    const initialElapsed = Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000);
    setElapsed(initialElapsed);

    // Update every second
    const interval = setInterval(() => {
      const elapsedFromStore = getElapsedTime(completionId);
      if (elapsedFromStore > 0) {
        setElapsed(elapsedFromStore);
      } else {
        // Fallback if store timer not initialized
        setElapsed(Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000));
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [completionId, startedAt, getElapsedTime]);

  return (
    <span className="text-yellow-500 font-mono font-bold">
      {formatTime(elapsed)}
    </span>
  );
};

export default function DashboardPage() {
  const { 
    balance, 
    dashboard,
    activeCompletions,
    fetchDashboard, 
    fetchMyActiveTasks,
    isLoading 
  } = useAppStore();
  const { user, logout } = useUserStore();
  const router = useRouter();

  // Track previous balance to detect real changes
  const prevBalanceRef = useRef(balance);
  const [displayBalance, setDisplayBalance] = useState(balance);
  
  useEffect(() => {
    // Only update display balance if it actually changed
    if (balance !== prevBalanceRef.current) {
      setDisplayBalance(balance);
      prevBalanceRef.current = balance;
    }
  }, [balance]);

  useEffect(() => {
    fetchDashboard();
    fetchMyActiveTasks();
    
    // Poll for updates every 30 seconds - silent update, no visual disruption
    const interval = setInterval(() => {
      fetchDashboard();
      fetchMyActiveTasks();
    }, 30000);
    
    return () => clearInterval(interval);
  }, [fetchDashboard, fetchMyActiveTasks]);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const stats = dashboard?.stats;

  return (
    <div className="p-4 space-y-6 animate-in fade-in duration-500 pb-24">
      <header className="flex justify-between items-center py-2">
        <div>
          <p className="text-zinc-500 text-xs font-bold uppercase tracking-widest">WELCOME BACK</p>
          <h1 className="text-xl font-black text-white uppercase italic">{user?.email.split('@')[0]}</h1>
        </div>
        <button 
          onClick={handleLogout}
          className="p-2 bg-zinc-900 border border-zinc-800 rounded-lg text-zinc-500 hover:text-red-500 transition-colors"
        >
          <LogOut size={20} />
        </button>
      </header>

      {/* BALANCE CARD - Fixed height to prevent layout shift */}
      <div className="relative overflow-hidden bg-yellow-500 rounded-2xl p-6 shadow-[0_10px_40px_rgba(234,179,8,0.3)] h-[140px]">
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-1">
            <Star size={16} className="text-black fill-black" />
            <span className="text-black text-xs font-black uppercase tracking-tighter">Current Balance</span>
          </div>
          <div className="flex items-end gap-2 h-[60px]">
            <span className="text-6xl font-black text-black leading-none italic">
              {isLoading ? <span className="opacity-50">-</span> : <AnimatedBalance value={displayBalance} />}
            </span>
            <span className="text-black font-black uppercase tracking-widest text-sm mb-1 italic">STARS</span>
          </div>
        </div>
        <div className="absolute -right-10 -bottom-10 opacity-10">
          <Star size={200} className="text-black fill-black" />
        </div>
      </div>

      {/* STATS GRID - Fixed heights */}
      <div className="grid grid-cols-2 gap-4">
        <StatCard icon={Trophy} label="Total Earned" value={stats?.total_earned || 0} />
        <StatCard icon={Zap} label="Spent" value={stats?.total_spent || 0} />
        <StatCard icon={Target} label="Completed" value={stats?.tasks_completed || 0} />
        <StatCard icon={Hourglass} label="Pending Review" value={stats?.tasks_pending_review || 0} />
      </div>

      {/* ACTIVE TASKS */}
      {activeCompletions.length > 0 && (
        <section className="space-y-4">
          <div className="flex justify-between items-center px-1">
            <h2 className="text-sm font-black text-yellow-500 uppercase tracking-widest italic flex items-center gap-2">
              <Clock size={16} />
              IN PROGRESS ({activeCompletions.length})
            </h2>
            <button 
              onClick={() => router.push('/tasks')}
              className="text-xs font-black text-zinc-500 uppercase tracking-tighter"
            >
              VIEW ALL
            </button>
          </div>
          <div className="grid gap-3">
            {activeCompletions.slice(0, 2).map(completion => (
              <div 
                key={completion.id} 
                onClick={() => router.push('/tasks')}
                className="bg-zinc-900 border border-yellow-500/30 rounded-xl p-4 cursor-pointer hover:border-yellow-500/60 transition-colors"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-bold text-white">{completion.task?.title}</h3>
                    <p className="text-zinc-500 text-sm mt-1 line-clamp-1">{completion.task?.description}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-yellow-500 text-[10px] uppercase font-bold block">active</span>
                    <TaskTimer completionId={completion.id} startedAt={completion.started_at || ''} />
                  </div>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <Clock size={12} className="text-zinc-600" />
                  <span className="text-zinc-600 text-[10px]">
                    Started {new Date(completion.started_at || '').toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* RECENT HISTORY */}
      {dashboard?.recent_history && dashboard.recent_history.length > 0 && (
        <section className="space-y-4">
          <div className="flex justify-between items-center px-1">
            <h2 className="text-sm font-black text-zinc-500 uppercase tracking-widest italic flex items-center gap-2">
              <History size={16} />
              RECENT ACTIVITY
            </h2>
          </div>
          <div className="space-y-2">
            {dashboard.recent_history.slice(0, 5).map(item => (
              <div key={item.id} className="bg-zinc-900 border border-zinc-800 rounded-xl p-3 flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    item.amount > 0 ? 'bg-green-500/20 text-green-500' : 'bg-red-500/20 text-red-500'
                  }`}>
                    {item.amount > 0 ? <TrendingUp size={14} /> : <Zap size={14} />}
                  </div>
                  <div>
                    <p className="text-white text-sm font-bold">
                      {item.source.includes('task') ? 'Task Completed' : 
                       item.source.includes('reward') ? 'Reward Redeemed' : 'Points Adjustment'}
                    </p>
                    <p className="text-zinc-600 text-[10px]">
                      {new Date(item.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <span className={`font-bold ${item.amount > 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {item.amount > 0 ? '+' : ''}{item.amount}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* COMPLETED TASKS PREVIEW */}
      {dashboard?.completed_tasks && dashboard.completed_tasks.length > 0 && (
        <section className="space-y-4">
          <div className="flex justify-between items-center px-1">
            <h2 className="text-sm font-black text-green-500 uppercase tracking-widest italic flex items-center gap-2">
              <CheckCircle size={16} />
              RECENTLY COMPLETED
            </h2>
          </div>
          <div className="space-y-2">
            {dashboard.completed_tasks.slice(0, 3).map(completion => (
              <div key={completion.id} className="bg-zinc-900/50 border border-zinc-800/50 rounded-xl p-3">
                <div className="flex justify-between items-start">
                  <h3 className="text-white text-sm font-bold">{completion.task?.title}</h3>
                  <span className="text-yellow-500 text-[10px] font-bold">+{completion.points_awarded || 0}★</span>
                </div>
                <p className="text-zinc-500 text-[10px] mt-1">
                  {completion.status === 'approved' ? 'Approved' : 'Pending review'} • {' '}
                  {new Date(completion.created_at).toLocaleDateString()}
                  {completion.time_spent ? ` • ${formatTime(completion.time_spent)}` : ''}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* EMPTY STATE */}
      {!isLoading && activeCompletions.length === 0 && 
       (!dashboard?.completed_tasks || dashboard.completed_tasks.length === 0) && (
        <div className="bg-zinc-900/50 border border-zinc-800/50 border-dashed rounded-xl p-8 text-center">
          <Target className="mx-auto text-zinc-600 mb-4" size={40} />
          <p className="text-zinc-500 text-sm font-bold uppercase tracking-widest">NO TASKS YET</p>
          <button 
            onClick={() => router.push('/tasks')}
            className="mt-4 bg-yellow-500 text-black px-6 py-2 rounded-lg font-bold text-sm uppercase tracking-tighter"
          >
            START YOUR FIRST TASK
          </button>
        </div>
      )}
    </div>
  );
}
