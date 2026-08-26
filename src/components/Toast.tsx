import React, { useEffect } from 'react';
import { motion } from 'motion/react';
import { CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';

interface ToastProps {
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  onClose: () => void;
}

export const Toast: React.FC<ToastProps> = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, 4000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const config = {
    success: {
      bg: 'bg-surface border-green-light text-green',
      icon: <CheckCircle className="w-5 h-5 text-green" />
    },
    error: {
      bg: 'bg-surface border-red-200 text-red-600',
      icon: <AlertCircle className="w-5 h-5 text-red-600" />
    },
    info: {
      bg: 'bg-surface border-blue-200 text-blue-600',
      icon: <Info className="w-5 h-5 text-blue-600" />
    },
    warning: {
      bg: 'bg-surface border-amber-200 text-amber-600',
      icon: <AlertTriangle className="w-5 h-5 text-amber-600" />
    }
  };

  const current = config[type] || config.info;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -10, scale: 0.95 }}
      transition={{ duration: 0.2 }}
      className={`flex items-center gap-3 px-4 py-3 rounded-xl border shadow-sm pointer-events-auto max-w-sm font-sans ${current.bg}`}
    >
      <div className="shrink-0">{current.icon}</div>
      <p className="font-sans text-xs font-semibold text-text leading-tight">{message}</p>
    </motion.div>
  );
};
