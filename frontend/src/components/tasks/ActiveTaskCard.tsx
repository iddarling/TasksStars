'use client';

import React, { useState, useEffect } from 'react';
import { TaskCompletion } from '@/types';
import { useAppStore } from '@/store/appStore';
import { Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react';

interface ActiveTaskCardProps {
  completion: TaskCompletion;
}

const ActiveTaskCard: React.FC<ActiveTaskCardProps> = ({ completion }) => {
  const { completeTask, cancelTask, getElapsedTime, isLoading } = useAppStore();
  const [elapsedTime, setElapsedTime] = useState(0);
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [proof, setProof] = useState('');

  useEffect(() => {
    // Update elapsed time every second
    const interval = setInterval(() => {
      setElapsedTime(getElapsedTime(completion.id));
    }, 1000);

    return () => clearInterval(interval);
  }, [completion.id, getElapsedTime]);

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleComplete = async () => {
    if (!proof.trim()) return;
    
    try {
      await completeTask(completion.task_id, { proof });
      setShowCompleteModal(false);
    } catch (error) {
      console.error('Failed to complete task', error);
    }
  };

  const handleCancel = async () => {
    try {
      await cancelTask(completion.task_id);
    } catch (error) {
      console.error('Failed to cancel task', error);
    }
  };

  return (
    <>
      <div className="bg-zinc-900 border border-yellow-500/30 rounded-xl p-4">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-bold text-white">{completion.task?.title || 'Task'}</h3>
            <p className="text-zinc-400 text-sm mt-1">{completion.task?.description}</p>
          </div>
          <span className="flex items-center gap-1 text-yellow-500">
            <Clock size={14} />
            <span className="text-[10px] uppercase font-bold">in progress</span>
          </span>
        </div>

        {/* Timer */}
        <div className="mt-4 bg-zinc-950 rounded-lg p-4 text-center">
          <p className="text-zinc-500 text-[10px] uppercase tracking-widest mb-1">Time Elapsed</p>
          <p className="text-3xl font-mono font-bold text-yellow-500">
            {formatTime(elapsedTime)}
          </p>
        </div>

        {/* Points */}
        <div className="flex justify-between items-center mt-4">
          <div className="flex items-center gap-1">
            <span className="text-yellow-500 font-bold">{completion.task?.points || 0}</span>
            <span className="text-xs text-zinc-500 uppercase">stars reward</span>
          </div>
          {completion.task?.requires_review && (
            <span className="text-[10px] text-zinc-500 bg-zinc-800 px-2 py-1 rounded">
              requires review
            </span>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 mt-4">
          <button
            onClick={() => setShowCompleteModal(true)}
            disabled={isLoading}
            className="flex-1 bg-green-500 text-black font-bold py-3 rounded-lg hover:bg-green-400 transition-colors flex items-center justify-center gap-2"
          >
            {isLoading ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle size={16} />}
            COMPLETE
          </button>
          <button
            onClick={handleCancel}
            disabled={isLoading}
            className="px-4 bg-zinc-800 text-zinc-400 font-bold py-3 rounded-lg hover:bg-zinc-700 transition-colors"
          >
            <XCircle size={16} />
          </button>
        </div>
      </div>

      {/* Complete Task Modal */}
      {showCompleteModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 w-full max-w-md">
            <h3 className="text-xl font-bold text-white mb-4">Complete Task</h3>
            <p className="text-zinc-400 text-sm mb-4">
              Provide proof of completion for &quot;{completion.task?.title}&quot;
            </p>
            
            <textarea
              value={proof}
              onChange={(e) => setProof(e.target.value)}
              placeholder="Describe what you did or provide proof..."
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-4 text-white min-h-[120px] focus:outline-none focus:border-yellow-500 transition-colors"
            />

            <div className="flex gap-2 mt-6">
              <button
                onClick={() => setShowCompleteModal(false)}
                className="flex-1 bg-zinc-800 text-white font-bold py-3 rounded-xl hover:bg-zinc-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleComplete}
                disabled={!proof.trim() || isLoading}
                className="flex-1 bg-yellow-500 text-black font-bold py-3 rounded-xl hover:bg-yellow-400 transition-colors disabled:opacity-50"
              >
                {isLoading ? <Loader2 size={16} className="animate-spin mx-auto" /> : 'Submit'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ActiveTaskCard;
