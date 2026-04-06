'use client';

import React, { useEffect, useState } from 'react';
import { useAppStore } from '@/store/appStore';
import { useSearchParams, useRouter } from 'next/navigation';
import TaskCard from '@/components/tasks/TaskCard';
import ActiveTaskCard from '@/components/tasks/ActiveTaskCard';
import SuggestTaskModal from '@/components/tasks/SuggestTaskModal';
import MiniCalendar from '@/components/MiniCalendar';
import { Search, Loader2, Plus, Clock, Calendar, X } from 'lucide-react';

// Helper to format seconds to HH:MM:SS
const formatTime = (seconds: number) => {
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

export default function TasksPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const dateFilter = searchParams.get('date');
  
  const { 
    tasks, 
    activeCompletions,
    pendingTasks,
    completedTasks,
    awaitingReviewTasks,
    fetchTasks, 
    fetchMyActiveTasks,
    fetchMyPendingTasks,
    fetchMyCompletedTasks,
    fetchMyAwaitingReviewTasks,
    startTask,
    wsClient,
    isLoading 
  } = useAppStore();
  
  const [filter, setFilter] = useState<'all' | 'daily' | 'one-time'>('all');
  const [search, setSearch] = useState('');
  const [showSuggestModal, setShowSuggestModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'available' | 'active' | 'pending' | 'review' | 'completed'>('available');
  const [showCalendar, setShowCalendar] = useState(false);

  useEffect(() => {
    fetchTasks();
    fetchMyActiveTasks();
    fetchMyPendingTasks();
    fetchMyAwaitingReviewTasks();
    fetchMyCompletedTasks();
  }, [fetchTasks, fetchMyActiveTasks, fetchMyPendingTasks, fetchMyAwaitingReviewTasks, fetchMyCompletedTasks]);

  // WebSocket listener for real-time updates
  useEffect(() => {
    if (!wsClient) return;

    const handleMessage = (message: { type: string; data?: any }) => {
      // Refresh tasks when new task is created (approved or auto-approved)
      if (message.type === 'task_suggested_by_user' || message.type === 'task_created') {
        console.log('New task created, refreshing tasks...');
        fetchTasks();
      }
    };

    wsClient.on('task_suggested_by_user', handleMessage);
    wsClient.on('task_created', handleMessage);
    
    return () => {
      wsClient.off('task_suggested_by_user', handleMessage);
      wsClient.off('task_created', handleMessage);
    };
  }, [wsClient, fetchTasks]);

  const filteredTasks = tasks.filter(task => {
    const matchesFilter = filter === 'all' || task.type === filter;
    const matchesSearch = task.title.toLowerCase().includes(search.toLowerCase()) || 
                          task.description.toLowerCase().includes(search.toLowerCase());
    
    // Date filtering - when date is selected, show ONLY tasks with deadline on that date
    let matchesDate = true;
    if (dateFilter && activeTab === 'available') {
      if (task.deadline) {
        // Check if task deadline matches the selected date
        const taskDeadline = new Date(task.deadline).toISOString().split('T')[0];
        matchesDate = taskDeadline === dateFilter;
      } else {
        // Tasks without deadline do NOT show when a specific date is selected
        matchesDate = false;
      }
    }
    
    return matchesFilter && matchesSearch && matchesDate && task.status === 'active';
  });

  const handleStartTask = async (taskId: number) => {
    try {
      await startTask(taskId);
      setActiveTab('active');
    } catch (error) {
      console.error('Failed to start task', error);
    }
  };

  return (
    <div className="p-4 space-y-6 animate-in slide-in-from-bottom-4 duration-500 pb-24">
      <header className="flex justify-between items-center py-2">
        <div>
          <h1 className="text-3xl font-black text-white uppercase italic tracking-tighter shadow-yellow-500/20 drop-shadow-lg">TASKS</h1>
          <p className="text-zinc-500 text-[10px] font-black uppercase tracking-[0.2em]">MISSION CONTROL</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowCalendar(!showCalendar)}
            className={`p-3 rounded-xl transition-colors ${showCalendar ? 'bg-yellow-500 text-black' : 'bg-zinc-900 text-yellow-500'}`}
          >
            <Calendar size={20} />
          </button>
          <button
            onClick={() => setShowSuggestModal(true)}
            className="bg-yellow-500 text-black p-3 rounded-xl hover:bg-yellow-400 transition-colors"
          >
            <Plus size={20} />
          </button>
        </div>
      </header>

      {/* DATE FILTER INDICATOR */}
      {dateFilter && (
        <div className="flex items-center justify-between bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-3">
          <div className="flex items-center gap-2">
            <Calendar size={16} className="text-yellow-500" />
            <span className="text-yellow-500 text-sm font-bold">
              Tasks for: {new Date(dateFilter).toLocaleDateString()}
            </span>
          </div>
          <button
            onClick={() => router.push('/tasks')}
            className="text-zinc-500 hover:text-white"
          >
            <X size={18} />
          </button>
        </div>
      )}

      {/* CALENDAR */}
      {showCalendar && (
        <MiniCalendar 
          selectedDate={dateFilter}
          onDateSelect={(date) => {
            if (date) {
              router.push(`/tasks?date=${date}`);
            } else {
              router.push('/tasks');
            }
            setShowCalendar(false);
          }}
        />
      )}

      {/* TABS */}
      <div className="flex gap-2 flex-wrap">
        {(['available', 'active', 'pending', 'review', 'completed'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-3 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all border min-w-[80px] ${
              activeTab === tab 
                ? 'bg-yellow-500 text-black border-yellow-500' 
                : 'bg-zinc-900 text-zinc-500 border-zinc-800'
            }`}
          >
            {tab}
            {tab === 'active' && activeCompletions.length > 0 && (
              <span className="ml-1 bg-red-500 text-white px-1.5 py-0.5 rounded-full text-[8px]">
                {activeCompletions.length}
              </span>
            )}
            {tab === 'available' && filteredTasks.length > 0 && (
              <span className="ml-1 bg-purple-500 text-white px-1.5 py-0.5 rounded-full text-[8px]">
                {filteredTasks.length}
              </span>
            )}
            {tab === 'pending' && pendingTasks.length > 0 && (
              <span className="ml-1 bg-blue-500 text-white px-1.5 py-0.5 rounded-full text-[8px]">
                {pendingTasks.length}
              </span>
            )}
            {tab === 'review' && awaitingReviewTasks.length > 0 && (
              <span className="ml-1 bg-orange-500 text-white px-1.5 py-0.5 rounded-full text-[8px]">
                {awaitingReviewTasks.length}
              </span>
            )}
            {tab === 'completed' && completedTasks.length > 0 && (
              <span className="ml-1 bg-green-500 text-white px-1.5 py-0.5 rounded-full text-[8px]">
                {completedTasks.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* AVAILABLE TASKS TAB */}
      {activeTab === 'available' && (
        <>
          {/* SEARCH & FILTER */}
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
              <input
                type="text"
                placeholder="SEARCH MISSIONS..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-xl py-4 pl-12 pr-4 text-white focus:outline-none focus:border-yellow-500 transition-colors uppercase font-bold tracking-wider placeholder:text-zinc-600 text-sm"
              />
            </div>

            <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
              {(['all', 'daily', 'one-time'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-6 py-2 rounded-full font-black text-[10px] uppercase tracking-widest transition-all whitespace-nowrap border ${
                    filter === f 
                      ? 'bg-yellow-500 text-black border-yellow-500' 
                      : 'bg-zinc-900 text-zinc-500 border-zinc-800 hover:border-zinc-700'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          {/* TASK LIST */}
          <div className="grid gap-4">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-20 text-yellow-500">
                <Loader2 size={40} className="animate-spin" />
                <p className="mt-4 text-[10px] font-black uppercase tracking-widest italic opacity-50">Loading Missions...</p>
              </div>
            ) : filteredTasks.length > 0 ? (
              filteredTasks.map(task => (
                <TaskCard 
                  key={task.id} 
                  task={task} 
                  onStart={handleStartTask}
                  showStartButton
                />
              ))
            ) : (
              <div className="text-center py-20 border-2 border-dashed border-zinc-900 rounded-3xl">
                <p className="text-zinc-500 text-xs font-black uppercase tracking-widest italic opacity-50">NO MISSIONS FOUND</p>
              </div>
            )}
          </div>
        </>
      )}

      {/* ACTIVE TASKS TAB */}
      {activeTab === 'active' && (
        <div className="grid gap-4">
          {activeCompletions.length > 0 ? (
            activeCompletions.map(completion => (
              <ActiveTaskCard key={completion.id} completion={completion} />
            ))
          ) : (
            <div className="text-center py-20 border-2 border-dashed border-zinc-900 rounded-3xl">
              <Clock className="mx-auto text-zinc-600 mb-4" size={40} />
              <p className="text-zinc-500 text-xs font-black uppercase tracking-widest italic opacity-50">NO ACTIVE MISSIONS</p>
              <p className="text-zinc-600 text-[10px] mt-2">Start a task to see it here</p>
            </div>
          )}
        </div>
      )}

      {/* PENDING TASKS TAB */}
      {activeTab === 'pending' && (
        <div className="grid gap-4">
          {pendingTasks.length > 0 ? (
            pendingTasks.map(task => (
              <div key={task.id} className="bg-zinc-900 border border-blue-500/30 rounded-xl p-4">
                <div className="flex justify-between items-start">
                  <h3 className="text-lg font-bold text-white">{task.title}</h3>
                  <span className="text-[10px] uppercase bg-blue-500/20 text-blue-400 px-2 py-1 rounded">
                    awaiting approval
                  </span>
                </div>
                <p className="text-zinc-400 text-sm mt-2">{task.description}</p>
                <div className="flex justify-between items-center mt-3">
                  <span className="text-yellow-500 font-bold">{task.points} stars</span>
                  <span className="text-zinc-600 text-[10px]">{task.type}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-20 border-2 border-dashed border-zinc-900 rounded-3xl">
              <p className="text-zinc-500 text-xs font-black uppercase tracking-widest italic opacity-50">NO PENDING TASKS</p>
            </div>
          )}
        </div>
      )}

      {/* REVIEW TAB - Tasks awaiting admin approval */}
      {activeTab === 'review' && (
        <div className="grid gap-4">
          {awaitingReviewTasks.length > 0 ? (
            awaitingReviewTasks.map(completion => (
              <div key={completion.id} className="bg-zinc-900 border border-orange-500/30 rounded-xl p-4">
                <div className="flex justify-between items-start">
                  <h3 className="text-lg font-bold text-white">{completion.task?.title || 'Unknown Task'}</h3>
                  <span className="text-[10px] uppercase bg-orange-500/20 text-orange-400 px-2 py-1 rounded">
                    awaiting review
                  </span>
                </div>
                <p className="text-zinc-400 text-sm mt-2">{completion.task?.description || ''}</p>
                <div className="flex justify-between items-center mt-3">
                  <div className="flex items-center gap-2">
                    <span className="text-yellow-500 font-bold">+{completion.task?.points || 0} stars pending</span>
                    {completion.time_spent ? (
                      <span className="text-zinc-500 text-[10px]">
                        {formatTime(completion.time_spent)}
                      </span>
                    ) : null}
                  </div>
                  <span className="text-zinc-600 text-[10px]">{completion.task?.type}</span>
                </div>
                {completion.proof && (
                  <p className="text-zinc-500 text-[10px] mt-2 italic">
                    Proof: {completion.proof}
                  </p>
                )}
              </div>
            ))
          ) : (
            <div className="text-center py-20 border-2 border-dashed border-zinc-900 rounded-3xl">
              <p className="text-zinc-500 text-xs font-black uppercase tracking-widest italic opacity-50">NO TASKS AWAITING REVIEW</p>
              <p className="text-zinc-600 text-[10px] mt-2">Complete tasks requiring review to see them here</p>
            </div>
          )}
        </div>
      )}

      {/* COMPLETED TASKS TAB */}
      {activeTab === 'completed' && (
        <div className="grid gap-4">
          {completedTasks.length > 0 ? (
            completedTasks.map(completion => (
              <div key={completion.id} className="bg-zinc-900 border border-green-500/30 rounded-xl p-4">
                <div className="flex justify-between items-start">
                  <h3 className="text-lg font-bold text-white">{completion.task?.title || 'Unknown Task'}</h3>
                  <span className="text-[10px] uppercase bg-green-500/20 text-green-400 px-2 py-1 rounded">
                    completed
                  </span>
                </div>
                <p className="text-zinc-400 text-sm mt-2">{completion.task?.description || ''}</p>
                <div className="flex justify-between items-center mt-3">
                  <div className="flex items-center gap-2">
                    <span className="text-green-500 font-bold">+{completion.points_awarded || completion.task?.points || 0} stars</span>
                    {completion.time_spent ? (
                      <span className="text-zinc-500 text-[10px]">
                        {formatTime(completion.time_spent)}
                      </span>
                    ) : null}
                  </div>
                  <span className="text-zinc-600 text-[10px]">{completion.task?.type}</span>
                </div>
                {completion.completed_at && (
                  <p className="text-zinc-600 text-[10px] mt-2">
                    Completed: {new Date(completion.completed_at).toLocaleDateString()}
                  </p>
                )}
              </div>
            ))
          ) : (
            <div className="text-center py-20 border-2 border-dashed border-zinc-900 rounded-3xl">
              <p className="text-zinc-500 text-xs font-black uppercase tracking-widest italic opacity-50">NO COMPLETED TASKS</p>
              <p className="text-zinc-600 text-[10px] mt-2">Complete tasks to see them here</p>
            </div>
          )}
        </div>
      )}

      {showSuggestModal && (
        <SuggestTaskModal onClose={() => setShowSuggestModal(false)} />
      )}
    </div>
  );
}
