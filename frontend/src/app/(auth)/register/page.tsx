'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Star, Mail, Lock, Loader2, ArrowRight } from 'lucide-react';
import api from '@/services/api';
import { useUserStore } from '@/store/userStore';

const registerSchema = z.object({
  email: z.string().email({ message: "Invalid email address" }),
  password: z.string().min(6, { message: "Password must be at least 6 characters" }),
  confirmPassword: z.string().min(6, { message: "Confirm your password" }),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const setUser = useUserStore((state) => state.setUser);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormValues) => {
    setIsLoading(true);
    setError(null);
    try {
      await api.post('/auth/register', {
        email: data.email,
        password: data.password,
      });
      
      const loginResponse = await api.post('/auth/login', {
        email: data.email,
        password: data.password,
      });
      
      const { access_token, refresh_token, user } = loginResponse.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      setUser(user);
      
      router.push('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center p-4 overflow-y-auto">
      <div className="w-full max-w-md space-y-8 py-8">
        <div className="text-center">
          <div className="inline-block p-4 bg-yellow-500 rounded-2xl shadow-[0_0_30px_rgba(234,179,8,0.3)] mb-4">
            <Star size={48} className="text-black fill-black" />
          </div>
          <h1 className="text-4xl font-black text-white tracking-tighter uppercase italic">TaskStars</h1>
          <p className="text-zinc-500 mt-2 font-medium tracking-wide">START YOUR JOURNEY</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" size={20} />
              <input
                {...register('email')}
                type="email"
                placeholder="EMAIL"
                className="w-full bg-zinc-900 border border-zinc-800 rounded-xl py-4 pl-12 pr-4 text-white focus:outline-none focus:border-yellow-500 transition-colors uppercase font-bold tracking-wider placeholder:text-zinc-600"
              />
            </div>
            {errors.email && <p className="text-red-500 text-xs pl-2 font-bold uppercase tracking-tight">{errors.email.message}</p>}
          </div>

          <div className="space-y-2">
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" size={20} />
              <input
                {...register('password')}
                type="password"
                placeholder="PASSWORD"
                className="w-full bg-zinc-900 border border-zinc-800 rounded-xl py-4 pl-12 pr-4 text-white focus:outline-none focus:border-yellow-500 transition-colors uppercase font-bold tracking-wider placeholder:text-zinc-600"
              />
            </div>
            {errors.password && <p className="text-red-500 text-xs pl-2 font-bold uppercase tracking-tight">{errors.password.message}</p>}
          </div>

          <div className="space-y-2">
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" size={20} />
              <input
                {...register('confirmPassword')}
                type="password"
                placeholder="CONFIRM PASSWORD"
                className="w-full bg-zinc-900 border border-zinc-800 rounded-xl py-4 pl-12 pr-4 text-white focus:outline-none focus:border-yellow-500 transition-colors uppercase font-bold tracking-wider placeholder:text-zinc-600"
              />
            </div>
            {errors.confirmPassword && <p className="text-red-500 text-xs pl-2 font-bold uppercase tracking-tight">{errors.confirmPassword.message}</p>}
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-3 text-red-500 text-sm font-bold uppercase text-center tracking-wider">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-yellow-500 text-black font-black py-4 rounded-xl flex items-center justify-center gap-2 hover:bg-yellow-400 transition-all uppercase tracking-widest shadow-[0_4px_20px_rgba(234,179,8,0.2)]"
          >
            {isLoading ? <Loader2 size={24} className="animate-spin" /> : (
              <>
                REGISTER <ArrowRight size={24} />
              </>
            )}
          </button>
        </form>

        <div className="text-center pt-4">
          <Link href="/login" className="text-zinc-500 hover:text-white transition-colors font-bold uppercase tracking-widest text-sm">
            ALREADY JOINED? <span className="text-yellow-500 underline underline-offset-4 decoration-2 ml-1">LOGIN</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
