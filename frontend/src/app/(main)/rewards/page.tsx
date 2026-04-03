'use client';

import React, { useEffect, useState } from 'react';
import { useAppStore } from '@/store/appStore';
import RewardCard from '@/components/shared/RewardCard';
import { Gift, Sparkles, Loader2, Plus, CheckCircle, Clock, History } from 'lucide-react';

export default function RewardsPage() {
  const { 
    rewards, 
    balance, 
    myRewardRequests,
    fetchRewards, 
    fetchBalance, 
    suggestReward,
    redeemReward,
    fetchMyRewardRequests,
    isLoading 
  } = useAppStore();
  
  const [activeTab, setActiveTab] = useState<'available' | 'my-requests'>('available');
  const [isSuggesting, setIsSuggesting] = useState(false);
  const [successModal, setSuccessModal] = useState(false);
  const [successReward, setSuccessReward] = useState<{title: string; cost: number} | null>(null);
  const [suggestData, setSuggestData] = useState({
    title: '',
    description: '',
    cost: 100,
  });

  useEffect(() => {
    fetchRewards();
    fetchBalance();
    fetchMyRewardRequests();
  }, [fetchRewards, fetchBalance, fetchMyRewardRequests]);

  const activeRewards = rewards.filter(r => r.status === 'active');
  const pendingRequests = myRewardRequests.filter(r => r.status === 'pending');
  const approvedRequests = myRewardRequests.filter(r => r.status === 'approved');

  const handleSuggest = async () => {
    if (!suggestData.title || !suggestData.description) return;
    
    try {
      await suggestReward(suggestData);
      setIsSuggesting(false);
      setSuggestData({ title: '', description: '', cost: 100 });
    } catch (error) {
      console.error('Failed to suggest reward', error);
    }
  };

  const handleRedeem = async (rewardId: number) => {
    const reward = activeRewards.find(r => r.id === rewardId);
    try {
      await redeemReward(rewardId);
      setSuccessReward(reward ? { title: reward.title, cost: reward.cost } : null);
      setSuccessModal(true);
      // Auto-close after 3 seconds
      setTimeout(() => setSuccessModal(false), 3000);
    } catch (error) {
      console.error('Failed to redeem reward', error);
      alert('Failed to redeem reward. Check your balance.');
    }
  };

  return (
    <div className="p-4 space-y-6 animate-in slide-in-from-bottom-4 duration-500 pb-24">
      <header className="flex justify-between items-end py-2">
        <div>
          <h1 className="text-3xl font-black text-white uppercase italic tracking-tighter shadow-yellow-500/20 drop-shadow-lg">REWARDS</h1>
          <p className="text-zinc-500 text-[10px] font-black uppercase tracking-[0.2em]">STAR EXCHANGE</p>
        </div>
        <div className="bg-yellow-500 rounded-lg px-3 py-1 flex items-center gap-1 shadow-[0_0_15px_rgba(234,179,8,0.3)]">
          <Sparkles size={14} className="text-black" />
          <span className="text-black text-sm font-black italic">{balance}</span>
        </div>
      </header>

      {/* TABS */}
      <div className="flex gap-2">
        {(['available', 'my-requests'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-3 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all border ${
              activeTab === tab 
                ? 'bg-yellow-500 text-black border-yellow-500' 
                : 'bg-zinc-900 text-zinc-500 border-zinc-800'
            }`}
          >
            {tab === 'available' ? 'SHOP' : 'MY REQUESTS'}
            {tab === 'my-requests' && pendingRequests.length > 0 && (
              <span className="ml-1 bg-blue-500 text-white px-1.5 py-0.5 rounded-full text-[8px]">
                {pendingRequests.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* AVAILABLE REWARDS */}
      {activeTab === 'available' && (
        <>
          <div className="grid gap-4">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-20 text-yellow-500">
                <Loader2 size={40} className="animate-spin" />
                <p className="mt-4 text-[10px] font-black uppercase tracking-widest italic opacity-50">Loading Rewards...</p>
              </div>
            ) : activeRewards.length > 0 ? (
              activeRewards.map(reward => (
                <RewardCard 
                  key={reward.id} 
                  reward={reward} 
                  canAfford={balance >= reward.cost} 
                  onRedeem={handleRedeem}
                />
              ))
            ) : (
              <div className="text-center py-20 border-2 border-dashed border-zinc-900 rounded-3xl">
                <Gift className="mx-auto text-zinc-800 mb-4" size={48} />
                <p className="text-zinc-500 text-xs font-black uppercase tracking-widest italic opacity-50">THE VAULT IS EMPTY</p>
              </div>
            )}
          </div>

          {/* SUGGEST REWARD BUTTON */}
          <button 
            onClick={() => setIsSuggesting(true)}
            className="w-full bg-zinc-900 border-2 border-zinc-800 border-dashed rounded-xl py-6 flex flex-col items-center justify-center gap-2 hover:border-yellow-500/50 hover:bg-zinc-800/50 transition-all text-zinc-500 hover:text-yellow-500 group"
          >
            <Plus size={32} className="group-hover:scale-110 transition-transform" />
            <span className="text-[10px] font-black uppercase tracking-widest italic">Suggest New Reward</span>
          </button>
        </>
      )}

      {/* MY REQUESTS */}
      {activeTab === 'my-requests' && (
        <div className="space-y-6">
          {/* Pending Requests */}
          {pendingRequests.length > 0 && (
            <section>
              <h3 className="text-sm font-black text-blue-500 uppercase tracking-widest mb-3 flex items-center gap-2">
                <Clock size={16} />
                PENDING ({pendingRequests.length})
              </h3>
              <div className="space-y-3">
                {pendingRequests.map(request => (
                  <div key={request.id} className="bg-zinc-900 border border-blue-500/30 rounded-xl p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-bold text-white">{request.reward_title || request.reward?.title || 'Reward'}</h4>
                        <p className="text-zinc-400 text-sm mt-1">{request.reward_description || request.reward?.description}</p>
                      </div>
                      <span className="text-yellow-500 font-bold">-{request.points_spent || request.reward?.cost || 0}★</span>
                    </div>
                    <div className="flex items-center gap-2 mt-3">
                      <span className="text-[10px] bg-blue-500/20 text-blue-400 px-2 py-1 rounded uppercase">
                        awaiting admin approval
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Approved/Earned Rewards */}
          {approvedRequests.length > 0 && (
            <section>
              <h3 className="text-sm font-black text-green-500 uppercase tracking-widest mb-3 flex items-center gap-2">
                <CheckCircle size={16} />
                EARNED ({approvedRequests.length})
              </h3>
              <div className="space-y-3">
                {approvedRequests.map(request => (
                  <div key={request.id} className="bg-zinc-900/50 border border-green-500/30 rounded-xl p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-bold text-white">{request.reward_title || request.reward?.title || 'Reward'}</h4>
                        <p className="text-zinc-400 text-sm mt-1">{request.reward_description || request.reward?.description}</p>
                      </div>
                      <CheckCircle size={16} className="text-green-500" />
                    </div>
                    <p className="text-zinc-600 text-[10px] mt-2">
                      Approved on {request.reviewed_at ? new Date(request.reviewed_at).toLocaleDateString() : 'N/A'}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {pendingRequests.length === 0 && approvedRequests.length === 0 && (
            <div className="text-center py-20 border-2 border-dashed border-zinc-900 rounded-3xl">
              <History className="mx-auto text-zinc-800 mb-4" size={48} />
              <p className="text-zinc-500 text-xs font-black uppercase tracking-widest italic opacity-50">NO REQUESTS YET</p>
              <button
                onClick={() => setActiveTab('available')}
                className="mt-4 text-yellow-500 text-xs font-black uppercase tracking-tighter"
              >
                BROWSE REWARDS
              </button>
            </div>
          )}
        </div>
      )}

      {/* SUGGEST REWARD MODAL */}
      {isSuggesting && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-zinc-950 border border-zinc-800 rounded-3xl w-full max-w-sm p-6 space-y-6 animate-in zoom-in-95 duration-200">
            <h2 className="text-xl font-black text-white italic uppercase tracking-tight">SUGGEST REWARD</h2>
            <div className="space-y-4">
              <input 
                placeholder="REWARD TITLE"
                value={suggestData.title}
                onChange={(e) => setSuggestData({ ...suggestData, title: e.target.value })}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-white font-bold uppercase tracking-widest text-xs focus:border-yellow-500 transition-colors focus:outline-none"
              />
              <textarea 
                placeholder="DESCRIPTION"
                value={suggestData.description}
                onChange={(e) => setSuggestData({ ...suggestData, description: e.target.value })}
                rows={3}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-white font-bold uppercase tracking-widest text-xs focus:border-yellow-500 transition-colors focus:outline-none"
              />
              <div>
                <label className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider block mb-2">
                  Suggested Cost (stars)
                </label>
                <input 
                  type="number"
                  value={suggestData.cost}
                  onChange={(e) => setSuggestData({ ...suggestData, cost: parseInt(e.target.value) || 0 })}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-white font-bold text-sm focus:border-yellow-500 transition-colors focus:outline-none"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <button 
                onClick={() => setIsSuggesting(false)}
                className="flex-1 bg-zinc-900 text-zinc-500 font-black py-4 rounded-xl uppercase tracking-widest text-[10px]"
              >
                CANCEL
              </button>
              <button 
                onClick={handleSuggest}
                disabled={!suggestData.title || !suggestData.description || isLoading}
                className="flex-1 bg-yellow-500 text-black font-black py-4 rounded-xl uppercase tracking-widest text-[10px] disabled:opacity-50"
              >
                {isLoading ? <Loader2 size={16} className="animate-spin mx-auto" /> : 'SUBMIT'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SUCCESS MODAL */}
      {successModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-zinc-950 border border-green-500/30 rounded-3xl w-full max-w-sm p-8 space-y-6 animate-in zoom-in-95 duration-300">
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center">
                <CheckCircle size={40} className="text-green-500" />
              </div>
              <div>
                <h2 className="text-xl font-black text-white italic uppercase tracking-tight">REQUEST SENT!</h2>
                <p className="text-zinc-400 text-sm mt-2">
                  Your request for <span className="text-yellow-500 font-bold">{successReward?.title}</span> ({successReward?.cost}★) has been submitted.
                </p>
              </div>
              <p className="text-zinc-500 text-[10px] uppercase tracking-widest">
                Waiting for admin approval
              </p>
            </div>
            <button 
              onClick={() => setSuccessModal(false)}
              className="w-full bg-green-500 text-black font-black py-4 rounded-xl uppercase tracking-widest text-[10px]"
            >
              AWESOME!
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
