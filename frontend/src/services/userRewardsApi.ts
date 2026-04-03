import api from './api';
import {
  Reward,
  RewardRequest,
} from '../types';

export interface SuggestRewardData {
  title: string;
  description: string;
  cost: number;
}

export const userRewardsApi = {
  // Get available rewards
  getAvailable: (): Promise<Reward[]> =>
    api.get('/rewards/').then(r => r.data),

  // Suggest new reward
  suggestReward: (data: SuggestRewardData): Promise<Reward> =>
    api.post('/rewards/', data).then(r => r.data),

  // Redeem reward
  redeemReward: (rewardId: number): Promise<RewardRequest> =>
    api.post(`/rewards/${rewardId}/redeem`).then(r => r.data),

  // Get my reward requests
  getMyRequests: (): Promise<RewardRequest[]> =>
    api.get('/rewards/my-requests').then(r => r.data),
};
