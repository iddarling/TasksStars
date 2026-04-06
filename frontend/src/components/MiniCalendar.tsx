'use client';

import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon } from 'lucide-react';
import { userTasksApi } from '@/services/userTasksApi';

interface MiniCalendarProps {
  onDateSelect?: (date: string | null) => void;
  selectedDate?: string | null;
}

export default function MiniCalendar({ onDateSelect, selectedDate }: MiniCalendarProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [datesWithTasks, setDatesWithTasks] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth() + 1; // 1-12

  useEffect(() => {
    loadCalendarData();
  }, [year, month]);

  const loadCalendarData = async () => {
    setLoading(true);
    try {
      const data = await userTasksApi.getCalendar(year, month);
      setDatesWithTasks(data.dates_with_tasks);
    } catch (error) {
      console.error('Failed to load calendar data', error);
    } finally {
      setLoading(false);
    }
  };

  const getDaysInMonth = (year: number, month: number) => {
    return new Date(year, month, 0).getDate();
  };

  const getFirstDayOfMonth = (year: number, month: number) => {
    return new Date(year, month - 1, 1).getDay();
  };

  const daysInMonth = getDaysInMonth(year, month);
  const firstDay = getFirstDayOfMonth(year, month);

  const handlePrevMonth = () => {
    setCurrentDate(new Date(year, month - 2, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(year, month, 1));
  };

  const handleDateClick = (day: number) => {
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    if (selectedDate === dateStr) {
      onDateSelect?.(null); // Deselect
    } else {
      onDateSelect?.(dateStr);
    }
  };

  const handleTodayClick = () => {
    const today = new Date();
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    setCurrentDate(today);
    onDateSelect?.(todayStr);
  };

  const weekDays = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];
  const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

  const today = new Date();
  const isTodayMonth = today.getFullYear() === year && today.getMonth() + 1 === month;
  const todayDate = today.getDate();

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <CalendarIcon size={16} className="text-yellow-500" />
          <span className="text-white font-bold text-sm">
            {monthNames[month - 1]} {year}
          </span>
        </div>
        <div className="flex gap-1">
          <button
            onClick={handlePrevMonth}
            className="p-1.5 hover:bg-zinc-800 rounded-lg transition-colors"
          >
            <ChevronLeft size={16} className="text-zinc-400" />
          </button>
          <button
            onClick={handleTodayClick}
            className="text-[10px] font-black uppercase tracking-wider text-yellow-500 hover:text-yellow-400 px-2"
          >
            Today
          </button>
          <button
            onClick={handleNextMonth}
            className="p-1.5 hover:bg-zinc-800 rounded-lg transition-colors"
          >
            <ChevronRight size={16} className="text-zinc-400" />
          </button>
        </div>
      </div>

      {/* Week days header */}
      <div className="grid grid-cols-7 gap-1 mb-2">
        {weekDays.map((day) => (
          <div
            key={day}
            className="text-center text-[10px] font-black uppercase tracking-wider text-zinc-500"
          >
            {day}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-1">
        {/* Empty cells for days before the first day of month */}
        {Array.from({ length: firstDay }).map((_, index) => (
          <div key={`empty-${index}`} className="aspect-square" />
        ))}

        {/* Days */}
        {Array.from({ length: daysInMonth }).map((_, index) => {
          const day = index + 1;
          const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
          const isSelected = selectedDate === dateStr;
          const hasTask = datesWithTasks.includes(day);
          const isToday = isTodayMonth && day === todayDate;

          return (
            <button
              key={day}
              onClick={() => handleDateClick(day)}
              className={`
                aspect-square rounded-lg text-sm font-bold relative
                transition-all duration-200
                ${isSelected
                  ? 'bg-yellow-500 text-black'
                  : isToday
                    ? 'bg-yellow-500/20 text-yellow-500 border border-yellow-500/50'
                    : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                }
              `}
            >
              {day}
              {hasTask && !isSelected && (
                <span className="absolute bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 bg-yellow-500 rounded-full" />
              )}
            </button>
          );
        })}
      </div>

      {selectedDate && (
        <div className="mt-4 pt-3 border-t border-zinc-800">
          <button
            onClick={() => onDateSelect?.(null)}
            className="w-full text-[10px] font-black uppercase tracking-wider text-zinc-500 hover:text-white transition-colors"
          >
            Show all tasks
          </button>
        </div>
      )}
    </div>
  );
}
