import React from 'react';
import { Reward } from '@/types';
import { Gift, ShoppingCart } from 'lucide-react';

interface RewardCardProps {
  reward: Reward;
  onRedeem?: (id: number) => void;
  canAfford: boolean;
}

const RewardCard: React.FC<RewardCardProps> = ({ reward, onRedeem, canAfford }) => {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col gap-2 hover:border-yellow-500/50 transition-colors">
      <div className="flex justify-between items-start">
        <div className="bg-yellow-500/10 p-2 rounded-lg">
          <Gift className="text-yellow-500" size={24} />
        </div>
        <div className="text-right">
          <span className={`text-lg font-bold ${canAfford ? 'text-white' : 'text-zinc-500'}`}>
            {reward.cost}
          </span>
          <span className="text-[10px] text-zinc-500 block uppercase">stars</span>
        </div>
      </div>
      <h3 className="text-lg font-bold text-white mt-1 uppercase tracking-wider">{reward.title}</h3>
      <p className="text-zinc-400 text-sm">{reward.description}</p>
      {onRedeem && (
        <button
          onClick={() => onRedeem(reward.id)}
          disabled={!canAfford}
          className={`mt-2 w-full font-bold py-2 rounded-lg flex items-center justify-center gap-2 transition-all ${
            canAfford 
              ? 'bg-yellow-500 text-black hover:bg-yellow-400' 
              : 'bg-zinc-800 text-zinc-500 cursor-not-allowed'
          }`}
        >
          <ShoppingCart size={18} />
          REDEEM NOW
        </button>
      )}
    </div>
  );
};

export default RewardCard;
