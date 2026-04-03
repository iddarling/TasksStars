import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '../types';

interface UserState {
  user: User | null;
  setUser: (user: User | null) => void;
  isAuthenticated: boolean;
  logout: () => void;
  checkAuth: () => boolean;
}

export const useUserStore = create<UserState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      logout: () => {
        set({ user: null, isAuthenticated: false });
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
      },
      checkAuth: () => {
        if (typeof window === 'undefined') return false;
        const token = localStorage.getItem('access_token');
        const hasUser = !!get().user;
        const isAuth = !!token && hasUser;
        if (isAuth !== get().isAuthenticated) {
          set({ isAuthenticated: isAuth });
        }
        return isAuth;
      },
    }),
    {
      name: 'user-storage',
      partialize: (state) => ({ user: state.user }),
      onRehydrateStorage: () => (state) => {
        if (state && typeof window !== 'undefined') {
          const token = localStorage.getItem('access_token');
          state.isAuthenticated = !!token && !!state.user;
        }
      },
    }
  )
);
