'use client';

import React, { InputHTMLAttributes } from 'react';
import { LucideIcon } from 'lucide-react';

interface AuthInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  icon?: LucideIcon;
  error?: string;
}

export default function AuthInput({
  label,
  icon: Icon,
  error,
  className = '',
  ...props
}: AuthInputProps) {
  return (
    <div className="space-y-1.5 font-sans-body">
      <label className="block text-xs font-semibold text-[#E2EFE9]">
        {label}
      </label>
      <div className="relative flex items-center">
        {Icon && <Icon className="w-4 h-4 text-[#6B8F71] absolute left-3.5 shrink-0" />}
        <input
          {...props}
          className={`w-full bg-[#03241A] border ${
            error ? 'border-red-500/80 focus:border-red-400' : 'border-[#135A42] focus:border-[#2B7A54]'
          } rounded-xl ${
            Icon ? 'pl-10' : 'pl-4'
          } pr-4 h-[50px] text-sm text-[#F7F5EA] placeholder-[#6B8F71] focus:outline-none focus:ring-1 ${
            error ? 'focus:ring-red-500/30' : 'focus:ring-[#2B7A54]'
          } transition-all ${className}`}
        />
      </div>
      {error && (
        <p className="text-[11px] text-red-400 font-medium pt-0.5 animate-in fade-in duration-150">
          {error}
        </p>
      )}
    </div>
  );
}
