import React from 'react';
import { Task } from '@/types';
import { CheckCircle2, Clock, XCircle, Play, Hourglass } from 'lucide-react';

interface TaskCardProps {
  task: Task;
  onComplete?: (id: number) => void;
  onStart?: (id: number) => void;
  showStartButton?: boolean;
}

const statusIcons: Record<string, React.ReactNode> = {
  draft: <Clock className="text-gray-400" />,
  pending: <Hourglass className="text-blue-500" />,
  active: <Play className="text-green-500" />,
  in_progress: <Clock className="text-yellow-500" />,
  completed: <Clock className="text-purple-500" />,
  approved: <CheckCircle2 className="text-green-500" />,
  rejected: <XCircle className="text-red-500" />,
};

const statusLabels: Record<string, string> = {
  draft: 'draft',
  pending: 'pending approval',
  active: 'active',
  in_progress: 'in progress',
  completed: 'completed',
  approved: 'approved',
  rejected: 'rejected',
};

const TaskCard: React.FC<TaskCardProps> = ({ task, onComplete, onStart, showStartButton }) => {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col gap-2 hover:border-purple-500/50 transition-colors">
      <div className="flex justify-between items-start">
        <h3 className="text-lg font-bold text-white">{task.title}</h3>
        <span className="flex items-center gap-1">
          {statusIcons[task.status]}
          <span className="text-xs uppercase text-zinc-500">{statusLabels[task.status]}</span>
        </span>
      </div>
      <p className="text-zinc-400 text-sm line-clamp-2">{task.description}</p>
      <div className="flex justify-between items-center mt-2">
        <div className="flex items-center gap-1">
          <span className="text-yellow-500 font-bold">{task.points}</span>
          <span className="text-xs text-zinc-500 uppercase">stars</span>
        </div>
        <span className={`px-2 py-1 rounded text-[10px] uppercase font-bold ${
          task.type === 'daily' ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'
        }`}>
          {task.type}
        </span>
      </div>
      {showStartButton && task.status === 'active' && onStart && (
        <button
          onClick={() => onStart(task.id)}
          className="mt-2 w-full bg-yellow-500 text-black font-bold py-2 rounded-lg hover:bg-yellow-400 transition-colors flex items-center justify-center gap-2"
        >
          <Play size={16} />
          START TASK
        </button>
      )}
      {task.status === 'active' && onComplete && (
        <button
          onClick={() => onComplete(task.id)}
          className="mt-2 w-full bg-yellow-500 text-black font-bold py-2 rounded-lg hover:bg-yellow-400 transition-colors"
        >
          COMPLETE TASK
        </button>
      )}
    </div>
  );
};

export default TaskCard;
