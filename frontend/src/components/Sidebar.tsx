'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Plus,
  Search,
  MessageSquare,
  Trash2,
  Settings,
  LogOut,
  Info,
  Mail,
  FileText,
} from 'lucide-react';
import { Conversation } from '@/lib/api';
import IpSaktiLogo from '@/components/IpSaktiLogo';

interface SidebarProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
  onDeleteConversation: (id: string) => void;
  onOpenSettings?: () => void;
  onLogout?: () => void;
}

export default function Sidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  onOpenSettings,
  onLogout,
}: SidebarProps) {
  const pathname = usePathname();
  const [searchQuery, setSearchQuery] = useState('');

  const filteredConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <aside className="fixed top-0 left-0 bottom-0 w-[270px] bg-[#003E29] text-[#E2EFE9] flex flex-col z-30 shadow-xl border-r border-[#003322] font-sans-body">
      {/* Top Branding Area */}
      <div className="p-5 pb-4 border-b border-[#044D34]/60">
        <Link href="/" className="block">
          <IpSaktiLogo
            variant="dark"
            className="w-[195px] h-auto max-h-12 object-contain"
          />
        </Link>
        <div className="text-[10px] text-[#7B9F8E] mt-2 font-medium tracking-wide uppercase">
          Traditional Knowledge · IP · AYUSH
        </div>
      </div>

      {/* Action Button */}
      <div className="p-4 pb-2">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 bg-[#044D34] hover:bg-[#0A5F42] border border-[#1E5C46] text-white py-2.5 px-4 rounded-xl text-xs font-semibold transition-all duration-200 shadow-sm active:scale-[0.98] cursor-pointer"
        >
          <Plus className="w-4 h-4 text-[#A1C9B6]" />
          <span>+ New Research</span>
        </button>
      </div>

      {/* Main Content Sections — Goes Directly to Research History */}
      <div className="flex-1 overflow-y-auto px-4 py-2 space-y-4">
        {/* History Section */}
        <div className="space-y-2">
          <div className="text-[10px] font-bold tracking-widest text-[#7B9F8E] uppercase px-2">
            RESEARCH HISTORY
          </div>

          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-[#7B9F8E]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search history..."
              className="w-full bg-[#003322] border border-[#1E5C46] rounded-lg pl-8 pr-3 py-1.5 text-xs text-[#E2EFE9] placeholder-[#7B9F8E] focus:outline-none focus:border-[#519E7E] transition-colors"
            />
          </div>

          {/* Conversation List */}
          <div className="space-y-1 max-h-56 overflow-y-auto pr-1">
            {filteredConversations.length > 0 ? (
              filteredConversations.map((conv) => {
                const isActive = conv.id === activeConversationId;
                return (
                  <div
                    key={conv.id}
                    className={`group flex items-center justify-between rounded-lg px-2.5 py-2 text-xs transition-all cursor-pointer ${
                      isActive
                        ? 'bg-[#0A5F42] text-white font-medium border border-[#1E5C46]'
                        : 'text-[#CBE0D6] hover:bg-[#044D34]/50 hover:text-white'
                    }`}
                    onClick={() => onSelectConversation(conv.id)}
                  >
                    <div className="flex items-center gap-2 overflow-hidden">
                      <MessageSquare className="w-3.5 h-3.5 shrink-0 text-[#7B9F8E]" />
                      <span className="truncate max-w-[150px]">{conv.title}</span>
                    </div>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteConversation(conv.id);
                      }}
                      title="Delete conversation"
                      className="opacity-0 group-hover:opacity-100 p-1 text-[#7B9F8E] hover:text-red-400 transition-opacity"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })
            ) : (
              <div className="text-[11px] text-[#7B9F8E] p-2 text-center italic">
                No research history
              </div>
            )}
          </div>

          <div className="text-right pt-0.5">
            <button
              onClick={() => {}}
              className="text-[11px] text-[#A1C9B6] hover:underline font-medium hover:text-white transition-colors cursor-pointer"
            >
              View all →
            </button>
          </div>
        </div>
      </div>

      {/* Bottom Footer & Support Controls */}
      <div className="p-4 pt-3 border-t border-[#044D34]/60 space-y-3">
        <div className="space-y-1">
          <div className="text-[10px] font-bold tracking-widest text-[#7B9F8E] uppercase px-1 mb-1.5">
            HELP &amp; SUPPORT
          </div>

          <Link
            href="/settings"
            className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-[#CBE0D6] hover:bg-[#044D34]/50 hover:text-white transition-colors"
          >
            <Settings className="w-4 h-4 text-[#A1C9B6]" />
            <span>Settings</span>
          </Link>

          <Link
            href="/about"
            className={`flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              pathname === '/about'
                ? 'bg-[#0A5F42] text-white font-semibold border border-[#1E5C46]'
                : 'text-[#CBE0D6] hover:bg-[#044D34]/50 hover:text-white'
            }`}
          >
            <Info className="w-4 h-4 text-[#A1C9B6]" />
            <span>About IP-SAKTI</span>
          </Link>

          <a
            href="mailto:support@ipsakti.gov.in"
            className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-[#CBE0D6] hover:bg-[#044D34]/50 hover:text-white transition-colors"
          >
            <Mail className="w-4 h-4 text-[#A1C9B6]" />
            <span>Contact Support</span>
          </a>

          <a
            href="#"
            onClick={(e) => {
              e.preventDefault();
              alert('Opening IP-SAKTI Sahayak Documentation...');
            }}
            className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-[#CBE0D6] hover:bg-[#044D34]/50 hover:text-white transition-colors"
          >
            <FileText className="w-4 h-4 text-[#A1C9B6]" />
            <span>Documentation</span>
          </a>

          <button
            onClick={onLogout || (() => (window.location.href = '/login'))}
            className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-[#CBE0D6] hover:bg-[#044D34]/50 hover:text-white transition-colors cursor-pointer text-left"
          >
            <LogOut className="w-4 h-4 text-amber-500" />
            <span>Logout</span>
          </button>
        </div>

        {/* Government of India Initiative Branding */}
        <div className="pt-2 text-center border-t border-[#044D34]/50">
          <div className="text-[9px] font-bold tracking-widest text-[#82A997] uppercase">
            GOVERNMENT OF INDIA INITIATIVE
          </div>
          <div className="text-[8px] text-[#7B9F8E] mt-0.5 tracking-wider uppercase">
            PEOPLE · KNOWLEDGE · NATURE · BHARAT
          </div>
        </div>
      </div>
    </aside>
  );
}
