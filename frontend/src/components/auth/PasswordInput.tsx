'use client';

import React, { useState, InputHTMLAttributes } from 'react';
import { Lock, Eye, EyeOff } from 'lucide-react';

interface PasswordInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export default function PasswordInput({
  label,
  error,
  className = '',
  ...props
}: PasswordInputProps) {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="space-y-1.5 font-sans-body">
      <label className="block text-xs font-semibold text-[#E2EFE9]">
        {label}
      </label>
      <div className="relative flex items-center">
        <Lock className="w-4 h-4 text-[#6B8F71] absolute left-3.5 shrink-0" />
        <input
          {...props}
          type={showPassword ? 'text' : 'password'}
          className={`w-full bg-[#03241A] border ${
            error ? 'border-red-500/80 focus:border-red-400' : 'border-[#135A42] focus:border-[#2B7A54]'
          } rounded-xl pl-10 pr-10 h-[50px] text-sm text-[#F7F5EA] placeholder-[#6B8F71] focus:outline-none focus:ring-1 ${
            error ? 'focus:ring-red-500/30' : 'focus:ring-[#2B7A54]'
          } transition-all ${className}`}
        />
        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          className="absolute right-3.5 text-[#6B8F71] hover:text-[#A1C9B6] transition-colors focus:outline-none cursor-pointer"
          aria-label={showPassword ? 'Hide password' : 'Show password'}
        >
          {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
        </button>
      </div>
      {error && (
        <p className="text-[11px] text-red-400 font-medium pt-0.5 animate-in fade-in duration-150">
          {error}
        </p>
      )}
    </div>
  );
}
