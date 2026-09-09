'use client';

import React, { useState, KeyboardEvent } from 'react';
import { Search, Send, Loader2, Globe } from 'lucide-react';

interface ChatInputBarProps {
  onSendMessage: (query: string) => void;
  isLoading?: boolean;
}

export default function ChatInputBar({ onSendMessage, isLoading = false }: ChatInputBarProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = () => {
    const trimmed = query.trim();
    if (!trimmed || isLoading) return;
    onSendMessage(trimmed);
    setQuery('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full relative z-20 my-4 font-sans-body">
      <div className="flex flex-col bg-white border border-[#C8D7C2] rounded-xl p-2 shadow-sm hover:shadow-md focus-within:border-[#003E29] focus-within:ring-1 focus-within:ring-[#003E29]/20 transition-all">
        <div className="flex items-center gap-3 px-3 py-1">
          <Search className="w-4 h-4 text-[#385246] shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="Ask about Traditional Knowledge, patents, AYUSH or ABS... (English / हिन्दी)"
            className="flex-1 bg-transparent py-2.5 text-sm text-[#003E29] placeholder-[#7C817A] focus:outline-none font-sans-body"
          />

          <button
            onClick={handleSubmit}
            disabled={!query.trim() || isLoading}
            aria-label="Submit research query"
            className="w-10 h-10 bg-[#003E29] hover:bg-[#044D34] disabled:bg-[#003E29]/30 text-white rounded-lg flex items-center justify-center transition-all duration-200 shrink-0 shadow-sm active:scale-95 cursor-pointer"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin text-white" />
            ) : (
              <Send className="w-4 h-4 text-white ml-0.5" />
            )}
          </button>
        </div>

        {/* Bottom Helper Bar */}
        <div className="flex items-center justify-between px-3 pt-1 pb-1 border-t border-[#C8D7C2]/40 text-[11px] text-[#7B9F8E]">
          <div className="flex items-center gap-1.5">
            <Globe className="w-3 h-3 text-[#385246]" />
            <span>Multilingual query support · Automatic Hindi/English translation</span>
          </div>
          <div className="hidden sm:block">Press Enter ↵ to submit</div>
        </div>
      </div>
    </div>
  );
}
