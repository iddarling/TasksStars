'use client';

import React, { useEffect } from 'react';
import { X, Bell, CheckCircle, Check } from 'lucide-react';
import { useAppStore } from '@/store/appStore';

interface NotificationsPanelProps {
  onClose: () => void;
}

const NotificationsPanel: React.FC<NotificationsPanelProps> = ({ onClose }) => {
  const { notifications, unreadNotificationsCount, fetchNotifications, markNotificationRead, markAllNotificationsRead } = useAppStore();

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'task_approved':
        return <CheckCircle className="text-green-500" size={20} />;
      case 'task_rejected':
        return <CheckCircle className="text-red-500" size={20} />;
      case 'completion_approved':
        return <CheckCircle className="text-green-500" size={20} />;
      case 'completion_rejected':
        return <CheckCircle className="text-red-500" size={20} />;
      case 'reward_approved':
        return <CheckCircle className="text-green-500" size={20} />;
      case 'reward_rejected':
        return <CheckCircle className="text-red-500" size={20} />;
      default:
        return <Bell className="text-yellow-500" size={20} />;
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
        onClick={onClose}
      />
      
      {/* Panel */}
      <div className="fixed bottom-0 left-0 right-0 bg-zinc-950 border-t border-zinc-800 rounded-t-3xl z-50 max-h-[80vh] overflow-hidden animate-in slide-in-from-bottom duration-300">
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b border-zinc-800">
          <div className="flex items-center gap-3">
            <Bell className="text-yellow-500" size={24} />
            <h2 className="text-lg font-bold text-white">Notifications</h2>
            {unreadNotificationsCount > 0 && (
              <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full font-bold">
                {unreadNotificationsCount}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {unreadNotificationsCount > 0 && (
              <button
                onClick={() => markAllNotificationsRead()}
                className="flex items-center gap-1 text-[10px] uppercase font-bold text-zinc-500 hover:text-yellow-500 transition-colors px-3 py-2"
              >
                <Check size={14} />
                Mark all read
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 text-zinc-500 hover:text-white transition-colors"
            >
              <X size={24} />
            </button>
          </div>
        </div>

        {/* Notifications List */}
        <div className="overflow-y-auto max-h-[60vh] p-4 space-y-3">
          {notifications.length === 0 ? (
            <div className="text-center py-12">
              <Bell className="mx-auto text-zinc-700 mb-4" size={48} />
              <p className="text-zinc-500 text-sm font-bold uppercase tracking-widest">No notifications</p>
            </div>
          ) : (
            notifications.map((notification) => (
              <div
                key={notification.id}
                onClick={() => markNotificationRead(notification.id)}
                className={`flex gap-3 p-4 rounded-xl border transition-all cursor-pointer ${
                  notification.is_read
                    ? 'bg-zinc-900/50 border-zinc-800/50 opacity-60'
                    : 'bg-zinc-900 border-yellow-500/30'
                }`}
              >
                <div className="flex-shrink-0 mt-0.5">
                  {getNotificationIcon(notification.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-bold text-white text-sm">{notification.title}</h3>
                  <p className="text-zinc-400 text-sm mt-1">{notification.message}</p>
                  <p className="text-zinc-600 text-[10px] mt-2">
                    {new Date(notification.created_at).toLocaleString()}
                  </p>
                </div>
                {!notification.is_read && (
                  <div className="flex-shrink-0 w-2 h-2 bg-yellow-500 rounded-full mt-2" />
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
};

export default NotificationsPanel;
