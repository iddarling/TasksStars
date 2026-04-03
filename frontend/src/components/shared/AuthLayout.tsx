'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useUserStore } from '@/store/userStore';
import BottomNav from '@/components/shared/BottomNav';
import { WebSocketProvider } from '@/components/providers/WebSocketProvider';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated } = useUserStore();
  const router = useRouter();
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const isAuthPage = pathname === '/login' || pathname === '/register';

  useEffect(() => {
    if (mounted) {
      if (!isAuthenticated && !isAuthPage) {
        router.push('/login');
      } else if (isAuthenticated && isAuthPage) {
        router.push('/');
      }
    }
  }, [isAuthenticated, isAuthPage, router, mounted]);

  if (!mounted) return null;

  return (
    <WebSocketProvider>
      <main className={`${!isAuthPage ? 'pb-20' : ''} max-w-lg mx-auto`}>
        {children}
      </main>
      {!isAuthPage && isAuthenticated && <BottomNav />}
    </WebSocketProvider>
  );
}
