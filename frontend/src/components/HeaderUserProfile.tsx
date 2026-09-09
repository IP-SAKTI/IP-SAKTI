'use client';

import React, { useState } from 'react';
import { User, ChevronDown, Settings, LogOut } from 'lucide-react';

interface HeaderUserProfileProps {
  userName?: string;
  userEmail?: string;
  onOpenSettings?: () => void;
  onLogout?: () => void;
}

export default function HeaderUserProfile({
  userName = 'manaswitha',
  userEmail = 'manaswitha@ipsakti.gov.in',
  onOpenSettings,
  onLogout,
}: HeaderUserProfileProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative inline-block text-left z-20">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 bg-[#FAFDF6] hover:bg-[#F4FAF0] border border-[#C8D7C2] px-3.5 py-1.5 rounded-lg text-sm font-medium text-[#003E29] shadow-sm transition-all active:scale-[0.99]"
      >
        <User className="w-4 h-4 text-[#003E29]" />
        <span className="truncate max-w-[130px]">{userName}</span>
        <ChevronDown className={`w-3.5 h-3.5 text-[#003E29] transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 bg-[#FAFDF6] border border-[#C8D7C2] rounded-xl shadow-lg p-2 z-50 animate-in fade-in zoom-in-95 duration-150">
          <div className="px-3 py-2 border-b border-[#C8D7C2]/60">
            <div className="font-semibold text-xs text-[#003E29]">{userName}</div>
            <div className="text-[11px] text-[#4A6357] truncate">{userEmail}</div>
          </div>

          <div className="pt-1.5 space-y-1">
            <button
              onClick={() => {
                setIsOpen(false);
                onOpenSettings?.();
              }}
              className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-[#003E29] hover:bg-[#EEF3E4] rounded-md transition-colors"
            >
              <Settings className="w-3.5 h-3.5 text-[#003E29]" />
              <span>Account Settings</span>
            </button>

            <button
              onClick={() => {
                setIsOpen(false);
                onLogout?.();
              }}
              className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-red-700 hover:bg-red-50 rounded-md transition-colors"
            >
              <LogOut className="w-3.5 h-3.5 text-red-600" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
