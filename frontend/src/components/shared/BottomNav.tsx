'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, CheckSquare, Gift, Settings, Bell } from 'lucide-react';
import { useUserStore } from '@/store/userStore';
import { useAppStore } from '@/store/appStore';
import NotificationsPanel from './NotificationsPanel';

const BottomNav = () => {
  const pathname = usePathname();
  const { user } = useUserStore();
  const { unreadNotificationsCount, fetchNotifications } = useAppStore();
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);

  useEffect(() => {
    if (user) {
      fetchNotifications();
      // Poll for notifications every 5 seconds
      const interval = setInterval(fetchNotifications, 5000);
      return () => clearInterval(interval);
    }
  }, [user, fetchNotifications]);

  const navItems = [
    { label: 'Home', href: '/', icon: LayoutDashboard },
    { label: 'Tasks', href: '/tasks', icon: CheckSquare },
    { label: 'Rewards', href: '/rewards', icon: Gift },
  ];

  if (user?.role === 'ADMIN') {
    navItems.push({ label: 'Admin', href: '/admin', icon: Settings });
  }

  return (
    <>
      <nav className="fixed bottom-0 left-0 right-0 bg-black border-t border-zinc-800 pb-safe z-40">
        <div className="flex justify-around items-center h-16">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-col items-center justify-center w-full h-full transition-colors ${
                  isActive ? 'text-yellow-500' : 'text-zinc-500 hover:text-zinc-300'
                }`}
              >
                <Icon size={24} />
                <span className="text-[10px] mt-1 uppercase tracking-wider">{item.label}</span>
              </Link>
            );
          })}
          
          {/* Notifications Bell */}
          <button
            onClick={() => setIsNotificationsOpen(true)}
            className="flex flex-col items-center justify-center w-full h-full transition-colors text-zinc-500 hover:text-zinc-300 relative"
          >
            <div className="relative">
              <Bell size={24} />
              {unreadNotificationsCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[8px] w-4 h-4 rounded-full flex items-center justify-center font-bold">
                  {unreadNotificationsCount > 9 ? '9+' : unreadNotificationsCount}
                </span>
              )}
            </div>
            <span className="text-[10px] mt-1 uppercase tracking-wider">Alerts</span>
          </button>
        </div>
      </nav>

      {/* Notifications Panel */}
      {isNotificationsOpen && (
        <NotificationsPanel onClose={() => setIsNotificationsOpen(false)} />
      )}
    </>
  );
};

export default BottomNav;
