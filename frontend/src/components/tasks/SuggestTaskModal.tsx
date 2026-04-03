'use client';

import React, { useState } from 'react';
import { useAppStore } from '@/store/appStore';
import { X, Loader2 } from 'lucide-react';

interface SuggestTaskModalProps {
  onClose: () => void;
}

const SuggestTaskModal: React.FC<SuggestTaskModalProps> = ({ onClose }) => {
  const { suggestTask, isLoading } = useAppStore();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState<'daily' | 'one-time'>('one-time');
  const [points, setPoints] = useState(10);
  const [requiresReview, setRequiresReview] = useState(true);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await suggestTask({
        title,
        description,
        type,
        points,
        requires_review: requiresReview,
      });
      onClose();
    } catch (error) {
      console.error('Failed to suggest task', error);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-white">Suggest New Task</h3>
          <button
            onClick={onClose}
            className="text-zinc-500 hover:text-white transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider block mb-2">
              Task Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter task title..."
              required
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-4 text-white focus:outline-none focus:border-yellow-500 transition-colors"
            />
          </div>

          <div>
            <label className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider block mb-2">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the task..."
              required
              rows={3}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-4 text-white focus:outline-none focus:border-yellow-500 transition-colors resize-none"
            />
          </div>

          <div>
            <label className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider block mb-2">
              Task Type
            </label>
            <div className="flex gap-2">
              {(['daily', 'one-time'] as const).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setType(t)}
                  className={`flex-1 py-3 rounded-xl font-bold text-[10px] uppercase tracking-widest transition-all border ${
                    type === t
                      ? 'bg-yellow-500 text-black border-yellow-500'
                      : 'bg-zinc-950 text-zinc-500 border-zinc-800'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider block mb-2">
              Points Reward
            </label>
            <input
              type="number"
              value={points}
              onChange={(e) => setPoints(parseInt(e.target.value) || 0)}
              min={1}
              max={1000}
              required
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-4 text-white focus:outline-none focus:border-yellow-500 transition-colors"
            />
          </div>

          <div className="flex items-center gap-3 p-4 bg-zinc-950 rounded-xl">
            <input
              type="checkbox"
              id="requiresReview"
              checked={requiresReview}
              onChange={(e) => setRequiresReview(e.target.checked)}
              className="w-5 h-5 rounded border-zinc-700 bg-zinc-800 text-yellow-500 focus:ring-yellow-500"
            />
            <label htmlFor="requiresReview" className="text-zinc-400 text-sm">
              Requires admin review before awarding points
            </label>
          </div>

          <div className="flex gap-2 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-zinc-800 text-white font-bold py-3 rounded-xl hover:bg-zinc-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !title.trim() || !description.trim()}
              className="flex-1 bg-yellow-500 text-black font-bold py-3 rounded-xl hover:bg-yellow-400 transition-colors disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 size={16} className="animate-spin mx-auto" />
              ) : (
                'Suggest Task'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SuggestTaskModal;
