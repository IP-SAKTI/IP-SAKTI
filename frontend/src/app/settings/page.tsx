'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Settings, User, Shield, Sliders, Database, Save, CheckCircle2, Leaf } from 'lucide-react';
import BotanicalBackground from '@/components/BotanicalBackground';
import HeaderUserProfile from '@/components/HeaderUserProfile';

export default function SettingsPage() {
  const [saved, setSaved] = useState(false);
  const [confidenceThreshold, setConfidenceThreshold] = useState('0.75');
  const [topK, setTopK] = useState('5');
  const [rerankerEnabled, setRerankerEnabled] = useState(true);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="min-h-screen w-full bg-[#EEF3E4] font-sans-body relative flex flex-col p-6 lg:p-12">
      <BotanicalBackground />

      <header className="max-w-4xl w-full mx-auto flex items-center justify-between mb-8 relative z-20">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-xs font-semibold text-[#003E29] bg-[#FAFDF6] border border-[#C8D7C2] px-3.5 py-2 rounded-lg hover:bg-[#F4FAF0] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </Link>

        <HeaderUserProfile />
      </header>

      <main className="max-w-4xl w-full mx-auto bg-[#FAFDF6] border border-[#C8D7C2] rounded-2xl p-8 lg:p-12 shadow-md relative z-10 space-y-6">
        <div className="border-b border-[#C8D7C2]/80 pb-6 flex items-center justify-between">
          <div>
            <div className="inline-flex items-center gap-1.5 bg-[#EEF3E4] text-[#003E29] text-xs font-bold px-3 py-1 rounded-md mb-2">
              <Settings className="w-3.5 h-3.5" />
              <span>System Configuration</span>
            </div>
            <h1 className="font-serif-heading text-3xl lg:text-4xl font-bold text-[#003E29]">
              Account & Research Pipeline Settings
            </h1>
            <p className="text-xs text-[#4A6357] mt-1">
              Manage user profile credentials and RAG retrieval confidence parameters
            </p>
          </div>
        </div>

        {saved && (
          <div className="bg-emerald-50 border border-emerald-200 text-emerald-900 rounded-lg p-3 text-xs font-semibold flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>Settings successfully saved and applied to research pipeline.</span>
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-6">
          {/* User Profile Section */}
          <div className="bg-white border border-[#C8D7C2] rounded-xl p-5 space-y-4">
            <div className="flex items-center gap-2 text-sm font-bold text-[#003E29]">
              <User className="w-4 h-4 text-[#003E29]" />
              <span>User Credentials</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block font-semibold text-[#003E29] mb-1">User Name</label>
                <input
                  type="text"
                  defaultValue="manaswitha"
                  className="w-full bg-[#EEF3E4]/40 border border-[#C8D7C2] rounded-lg p-2 text-[#003E29] font-medium"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#003E29] mb-1">Official Email</label>
                <input
                  type="email"
                  defaultValue="manaswitha@ipsakti.gov.in"
                  className="w-full bg-[#EEF3E4]/40 border border-[#C8D7C2] rounded-lg p-2 text-[#003E29] font-medium"
                />
              </div>
            </div>
          </div>

          {/* RAG Pipeline Parameters */}
          <div className="bg-white border border-[#C8D7C2] rounded-xl p-5 space-y-4">
            <div className="flex items-center gap-2 text-sm font-bold text-[#003E29]">
              <Sliders className="w-4 h-4 text-[#003E29]" />
              <span>RAG Retrieval & Abstention Parameters</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block font-semibold text-[#003E29] mb-1">
                  Confidence Threshold for Safe Abstention
                </label>
                <input
                  type="number"
                  step="0.05"
                  min="0.5"
                  max="0.95"
                  value={confidenceThreshold}
                  onChange={(e) => setConfidenceThreshold(e.target.value)}
                  className="w-full bg-white border border-[#C8D7C2] rounded-lg p-2 text-[#003E29]"
                />
                <p className="text-[11px] text-[#4A6357] mt-1">
                  Queries scoring below this confidence automatically trigger Human Facilitator escalation.
                </p>
              </div>

              <div>
                <label className="block font-semibold text-[#003E29] mb-1">
                  Top Grounded Evidence Chunks (Top-K)
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={topK}
                  onChange={(e) => setTopK(e.target.value)}
                  className="w-full bg-white border border-[#C8D7C2] rounded-lg p-2 text-[#003E29]"
                />
                <p className="text-[11px] text-[#4A6357] mt-1">
                  Maximum number of verified source evidence chunks passed to LLM.
                </p>
              </div>
            </div>

            <div className="pt-2 flex items-center gap-2">
              <input
                type="checkbox"
                id="reranker"
                checked={rerankerEnabled}
                onChange={(e) => setRerankerEnabled(e.target.checked)}
                className="rounded border-[#C8D7C2] text-[#003E29]"
              />
              <label htmlFor="reranker" className="text-xs text-[#003E29] font-medium cursor-pointer">
                Enable Cross-Encoder Reranking (`ms-marco-MiniLM-L-6-v2`)
              </label>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              className="flex items-center gap-2 bg-[#003E29] hover:bg-[#044D34] text-white font-semibold py-2.5 px-5 rounded-lg text-xs transition-all shadow-md active:scale-95"
            >
              <Save className="w-4 h-4" />
              <span>Save Configuration</span>
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
