'use client';

import React, { ButtonHTMLAttributes } from 'react';
import { ArrowRight, Loader2 } from 'lucide-react';

interface AuthButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  isLoading?: boolean;
}

export default function AuthButton({
  children,
  isLoading = false,
  className = '',
  disabled,
  ...props
}: AuthButtonProps) {
  return (
    <button
      {...props}
      disabled={disabled || isLoading}
      className={`w-full h-[50px] bg-[#2B7A54] hover:bg-[#236746] disabled:bg-[#2B7A54]/50 text-white font-semibold rounded-xl text-sm transition-all duration-200 shadow-sm flex items-center justify-center gap-2 mt-4 active:scale-[0.99] cursor-pointer disabled:cursor-not-allowed ${className}`}
    >
      {isLoading ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin text-white" />
          <span>Processing...</span>
        </>
      ) : (
        <>
          <span>{children}</span>
          <ArrowRight className="w-4 h-4" />
        </>
      )}
    </button>
  );
}
