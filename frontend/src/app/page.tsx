'use client';

import React, { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import HeaderUserProfile from '@/components/HeaderUserProfile';
import BotanicalBackground from '@/components/BotanicalBackground';
import FeatureCards from '@/components/FeatureCards';
import ChatInputBar from '@/components/ChatInputBar';
import ResearchPipelineProgress, { Stage } from '@/components/ResearchPipelineProgress';
import AnswerWorkspace from '@/components/AnswerWorkspace';
import { useAuth } from '@/context/AuthContext';
import {
  sendQueryToAPI,
  listConversations,
  getConversationDetailsAPI,
  saveConversationToStorage,
  deleteConversationFromStorage,
  APIQueryResponse,
  Conversation,
} from '@/lib/api';

const DEFAULT_STAGES: Stage[] = [
  { id: '1', label: 'Intent Classification', status: 'pending' },
  { id: '2', label: 'Jurisdiction Analysis', status: 'pending' },
  { id: '3', label: 'FAISS + BM25 Retrieval', status: 'pending' },
  { id: '4', label: 'RRF Reranking', status: 'pending' },
  { id: '5', label: 'Specialist Agent Synthesis', status: 'pending' },
  { id: '6', label: 'Citation Validation', status: 'pending' },
  { id: '7', label: 'Confidence Scoring', status: 'pending' },
];

export default function DashboardPage() {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const [activeResponse, setActiveResponse] = useState<APIQueryResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [stages, setStages] = useState<Stage[]>(DEFAULT_STAGES);

  // Load conversations scoped to user
  useEffect(() => {
    async function loadData() {
      try {
        const fetched = await listConversations(user?.id);
        setConversations(fetched || []);
      } catch (err) {
        console.warn('API backend conversation fetch fallback:', err);
      }
    }
    loadData();
  }, [user?.id]);

  const handleSendMessage = async (queryText: string) => {
    if (!queryText.trim() || isLoading) return;

    setCurrentQuery(queryText);
    setIsLoading(true);
    setActiveResponse(null);

    // Stage updates
    const initialStages: Stage[] = DEFAULT_STAGES.map((s) => ({
      ...s,
      status: s.id === '1' ? 'processing' : 'pending',
    }));
    setStages(initialStages);

    const interval = setInterval(() => {
      setStages((prev) => {
        const processingIdx = prev.findIndex((s) => s.status === 'processing');
        if (processingIdx !== -1 && processingIdx < prev.length - 1) {
          const updated = [...prev];
          updated[processingIdx] = { ...updated[processingIdx], status: 'complete' };
          updated[processingIdx + 1] = { ...updated[processingIdx + 1], status: 'processing' };
          return updated;
        }
        return prev;
      });
    }, 600);

    try {
      const response = await sendQueryToAPI(queryText);

      clearInterval(interval);

      setStages((prev) =>
        prev.map((s) => ({
          ...s,
          status: 'complete',
        }))
      );

      setActiveResponse(response);

      const newConv: Conversation = {
        id: Date.now().toString(),
        title: queryText.length > 28 ? queryText.slice(0, 28) + '...' : queryText,
        created_at: new Date().toISOString(),
        query: queryText,
        response: response,
      };

      setConversations((prev) => [newConv, ...prev]);
      setActiveConversationId(newConv.id);
      saveConversationToStorage(newConv, user?.id);
    } catch (err) {
      clearInterval(interval);
      console.error('Failed to process query:', err);

      setActiveResponse({
        query: queryText,
        answer: 'An unexpected connection error occurred while communicating with the research pipeline API. Please check your backend service status.',
        confidence: 0.0,
        evidence: [],
        citations: [],
        agents_invoked: ['Error Recovery'],
        is_abstention: true,
        disclaimer: 'Connection error. Please try again.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setActiveConversationId(null);
    setCurrentQuery('');
    setActiveResponse(null);
    setStages(DEFAULT_STAGES);
  };

  const handleSelectConversation = async (id: string) => {
    setActiveConversationId(id);
    const selected = conversations.find((c) => c.id === id);
    if (selected) {
      setCurrentQuery(selected.query || selected.title);
      if (selected.response) {
        setActiveResponse(selected.response);
      } else {
        try {
          const detail: any = await getConversationDetailsAPI(id, user?.id);
          if (detail && detail.messages && detail.messages.length > 0) {
            const lastAssistantMsg = [...detail.messages].reverse().find((m: any) => m.role === 'assistant');
            const userMsg = detail.messages.find((m: any) => m.role === 'user');
            if (userMsg) setCurrentQuery(userMsg.content);
            if (lastAssistantMsg && lastAssistantMsg.metadata?.response) {
              setActiveResponse(lastAssistantMsg.metadata.response);
            } else if (lastAssistantMsg) {
              setActiveResponse({
                query: userMsg?.content || selected.title,
                answer: lastAssistantMsg.content,
                confidence: 0.9,
                evidence: [],
                citations: [],
                agents_invoked: ['IP Agent'],
                is_abstention: false,
                disclaimer: 'Retrieved conversation history from database',
              });
            }
          }
        } catch (err) {
          console.error('Failed to load conversation details:', err);
        }
      }
    }
  };

  const handleDeleteConversation = (id: string) => {
    setConversations((prev) => prev.filter((c) => c.id !== id));
    deleteConversationFromStorage(id, user?.id);
    if (activeConversationId === id) {
      handleNewChat();
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#EEF3E4] font-sans-body relative flex">
      {/* Fixed Sidebar */}
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        onDeleteConversation={handleDeleteConversation}
        onOpenSettings={() => alert('Settings menu')}
        onLogout={() => (window.location.href = '/login')}
      />

      {/* Main Content Area */}
      <main className="flex-1 lg:ml-[270px] min-h-screen flex flex-col p-6 lg:p-10 relative z-10 overflow-y-auto">
        <BotanicalBackground />

        {/* Top Header Row with User Dropdown */}
        <header className="w-full flex items-center justify-between mb-6 relative z-20">
          <div className="text-xs font-semibold text-[#003E29] bg-white border border-[#C8D7C2] px-3.5 py-1.5 rounded-full shadow-xs">
            IP-SAKTI Sahayak · Enterprise AI Research Platform
          </div>

          <HeaderUserProfile />
        </header>

        {/* Hero Header Section */}
        <section className="max-w-4xl w-full mx-auto my-3 relative z-10 space-y-2">
          <div className="text-xs text-[#385246] font-serif-heading italic font-semibold">
            Sahayak, sahayak — "the one who assists"
          </div>

          <h1 className="font-serif-heading text-4xl lg:text-5xl font-bold text-[#003E29] tracking-tight leading-tight">
            Ask before you file.
          </h1>

          <p className="text-xs lg:text-sm text-[#385246] max-w-2xl leading-relaxed font-sans-body">
            Decision-support research for Traditional Knowledge, patent prior art, AYUSH regulatory compliance, and Access & Benefit Sharing — grounded in available source texts.
          </p>
        </section>

        {/* Feature Inquiry Cards */}
        <div className="max-w-4xl w-full mx-auto">
          <FeatureCards onSelectQuery={handleSendMessage} />
        </div>

        {/* Enterprise Research Search Box */}
        <div className="max-w-4xl w-full mx-auto">
          <ChatInputBar onSendMessage={handleSendMessage} isLoading={isLoading} />
        </div>

        {/* Pipeline Stage Progress Status */}
        {isLoading && (
          <div className="max-w-4xl w-full mx-auto">
            <ResearchPipelineProgress stages={stages} />
          </div>
        )}

        {/* Answer & Research Workspace */}
        {activeResponse && (
          <div className="max-w-4xl w-full mx-auto">
            <AnswerWorkspace
              query={currentQuery}
              response={activeResponse}
              onSaveResearch={() => alert('Research saved successfully.')}
            />
          </div>
        )}

        {/* Bottom Footer Note */}
        <footer className="max-w-4xl w-full mx-auto mt-auto pt-10 pb-4 text-center text-xs text-[#385246] italic font-medium relative z-10 border-t border-[#C8D7C2]/50">
          Nature's wisdom. Responsible innovation. · IP-SAKTI Sahayak Decision Support System
        </footer>
      </main>
    </div>
  );
}
