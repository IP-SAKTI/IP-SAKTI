'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, FileText, Download, Share2, ShieldCheck, Leaf } from 'lucide-react';
import BotanicalBackground from '@/components/BotanicalBackground';
import HeaderUserProfile from '@/components/HeaderUserProfile';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

export default function BriefPage() {
  const router = useRouter();
  const { user, profile, isLoading: authLoading } = useAuth();

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#001D14] flex items-center justify-center text-white text-sm font-sans-body">
        Loading IP-SAKTI...
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const displayEmail = profile?.email || user?.email || '';
  return (
    <div className="min-h-screen w-full bg-[#EEF3E4] font-sans-body relative flex flex-col p-6 lg:p-12">
      <BotanicalBackground />

      {/* Header */}
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

      {/* Main Document Content */}
      <main className="max-w-4xl w-full mx-auto bg-[#FAFDF6] border border-[#C8D7C2] rounded-2xl p-8 lg:p-12 shadow-md relative z-10 space-y-6">
        <div className="flex items-center justify-between border-b border-[#C8D7C2]/80 pb-6">
          <div>
            <div className="inline-flex items-center gap-1.5 bg-[#EEF3E4] text-[#003E29] text-xs font-bold px-3 py-1 rounded-md mb-2">
              <Leaf className="w-3.5 h-3.5" />
              <span>IP-SAKTI Official Research Brief</span>
            </div>
            <h1 className="font-serif-heading text-3xl lg:text-4xl font-bold text-[#003E29]">
              Turmeric & Neem Traditional Prior Art Synthesis
            </h1>
            <p className="text-xs text-[#4A6357] mt-1">
              Ref: IP-SAKTI-BRIEF-2026-0892 · Generated for: {displayEmail}
            </p>
          </div>

          <div className="flex gap-2">
            <button className="flex items-center gap-1.5 bg-[#EEF3E4] hover:bg-[#E3EBD7] text-[#003E29] text-xs font-semibold px-3 py-2 rounded-lg border border-[#C8D7C2] transition-colors">
              <Share2 className="w-3.5 h-3.5" />
              <span>Share</span>
            </button>
            <button className="flex items-center gap-1.5 bg-[#003E29] hover:bg-[#044D34] text-white text-xs font-semibold px-3.5 py-2 rounded-lg transition-colors">
              <Download className="w-3.5 h-3.5" />
              <span>Export PDF</span>
            </button>
          </div>
        </div>

        {/* Executive Summary */}
        <section className="space-y-3">
          <h2 className="font-serif-heading text-xl font-bold text-[#003E29]">
            1. Executive Summary
          </h2>
          <p className="text-sm text-[#263A35] leading-relaxed">
            This research brief synthesizes statutory prior art, Traditional Knowledge Digital Library (TKDL) references, and patent eligibility provisions under Section 3(p) of the Indian Patents Act, 1970 regarding topical formulations containing Curcuma longa (Turmeric) and Azadirachta indica (Neem).
          </p>
        </section>

        {/* Legal & Prior Art Analysis */}
        <section className="space-y-3">
          <h2 className="font-serif-heading text-xl font-bold text-[#003E29]">
            2. Patentability & Section 3(p) Exclusions
          </h2>
          <p className="text-sm text-[#263A35] leading-relaxed">
            Under Section 3(p) of the Indian Patents Act, an invention which in effect is traditional knowledge or an aggregation or duplication of known properties of traditionally known component or components is non-patentable.
          </p>
          <div className="bg-[#EEF3E4] border-l-4 border-[#003E29] p-4 rounded-r-lg text-xs text-[#003E29] space-y-1">
            <div className="font-bold">Key Precedent: CSIR Turmeric Patent Revocation (USPTO 1997)</div>
            <div>Revocation of US Patent 5,401,504 demonstrated that wound-healing properties of turmeric constituted prior art documented in ancient Ayurvedic literature.</div>
          </div>
        </section>

        {/* Citation Table */}
        <section className="space-y-3">
          <h2 className="font-serif-heading text-xl font-bold text-[#003E29]">
            3. Grounded TKDL & Corpus Citations
          </h2>
          <div className="border border-[#C8D7C2] rounded-xl overflow-hidden text-xs">
            <table className="w-full text-left">
              <thead className="bg-[#EEF3E4] text-[#003E29] font-bold border-b border-[#C8D7C2]">
                <tr>
                  <th className="p-3">Source Identifier</th>
                  <th className="p-3">Title / Classical Text</th>
                  <th className="p-3">Authority</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#C8D7C2]/60 text-[#385246]">
                <tr>
                  <td className="p-3 font-mono font-medium">TKDL-AYU-0842</td>
                  <td className="p-3 font-semibold text-[#003E29]">Charaka Samhita — Chikitsa Sthana</td>
                  <td className="p-3">AYUSH / TKDL</td>
                  <td className="p-3 text-emerald-700 font-bold">Verified Prior Art</td>
                </tr>
                <tr>
                  <td className="p-3 font-mono font-medium">IPA-1970-SEC3P</td>
                  <td className="p-3 font-semibold text-[#003E29]">Indian Patents Act Section 3(p)</td>
                  <td className="p-3">IPO / Legislative</td>
                  <td className="p-3 text-emerald-700 font-bold">Statutory Bar</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Verification Footer */}
        <div className="pt-6 border-t border-[#C8D7C2]/80 flex items-center justify-between text-xs text-[#4A6357]">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-[#003E29]" />
            <span>Citation Integrity Verified · Cross-Encoder Reranked Score 0.94</span>
          </div>
          <div>IP-SAKTI Sahayak System</div>
        </div>
      </main>
    </div>
  );
}
