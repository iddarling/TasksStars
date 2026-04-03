'use client';

import { useEffect, useState, useRef } from 'react';
import { motion, useSpring, useTransform } from 'framer-motion';

interface AnimatedBalanceProps {
  value: number;
  className?: string;
  duration?: number;
}

export function AnimatedBalance({ value, className = '', duration = 1.5 }: AnimatedBalanceProps) {
  const [displayValue, setDisplayValue] = useState(0);
  const previousValue = useRef(0);
  const isFirstRender = useRef(true);
  
  // Create a spring animation for smooth counting
  const spring = useSpring(0, {
    stiffness: 50,
    damping: 20,
  });
  
  // Transform spring value to integer display
  const rounded = useTransform(spring, (latest) => Math.round(latest));
  
  useEffect(() => {
    if (isFirstRender.current) {
      // First render: animate from 0 to value
      spring.set(value);
      isFirstRender.current = false;
    } else if (value !== previousValue.current) {
      // Value changed: animate from previous to new
      spring.set(value);
    }
    previousValue.current = value;
  }, [value, spring]);
  
  useEffect(() => {
    const unsubscribe = rounded.on('change', (latest) => {
      setDisplayValue(latest);
    });
    return unsubscribe;
  }, [rounded]);
  
  // Only pulse when value actually changes (not on first load)
  const shouldPulse = !isFirstRender.current && value !== previousValue.current;
  
  return (
    <motion.span 
      className={`inline-block tabular-nums ${className}`}
      initial={{ scale: 1 }}
      animate={{ 
        scale: shouldPulse ? [1, 1.1, 1] : 1,
      }}
      transition={{ duration: 0.3 }}
    >
      {displayValue}
    </motion.span>
  );
}
