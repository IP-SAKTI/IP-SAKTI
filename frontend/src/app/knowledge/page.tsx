'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Search, FileText, Database, Filter, ExternalLink, ShieldCheck } from 'lucide-react';
import HeaderUserProfile from '@/components/HeaderUserProfile';

export default function KnowledgePage() {
  const [filter, setFilter] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');

  const categories = ['All', 'IP & Patent', 'Traditional Knowledge', 'AYUSH Regulatory', 'ABS & Biodiversity'];

  const documents = [
    {
      id: 'TKDL-AYU-0842',
      title: 'Charaka Samhita — Chikitsa Sthana Formulation Records',
      category: 'Traditional Knowledge',
      authority: 'AYUSH / TKDL',
      chunks: 1420,
      indexedDate: '2026-08-15',
    },
    {
      id: 'IPA-1970-SEC3P',
      title: 'Indian Patents Act 1970 — Section 3(p) Exclusions',
      category: 'IP & Patent',
      authority: 'Indian Patent Office (IPO)',
      chunks: 85,
      indexedDate: '2026-08-10',
    },
    {
      id: 'AYUSH-RULE-158B',
      title: 'Drugs & Cosmetics Rules 1945 — Rule 158-B Licensing',
      category: 'AYUSH Regulatory',
      authority: 'Ministry of AYUSH',
      chunks: 310,
      indexedDate: '2026-08-20',
    },
    {
      id: 'BDA-2002-SEC6',
      title: 'Biological Diversity Act 2002 — Section 6 ABS Provisions',
      category: 'ABS & Biodiversity',
      authority: 'National Biodiversity Authority (NBA)',
      chunks: 490,
      indexedDate: '2026-08-18',
    },
    {
      id: 'SUSH-UTT-0412',
      title: 'Sushruta Samhita — Uttara Tantra Dermatological Formulations',
      category: 'Traditional Knowledge',
      authority: 'AYUSH / TKDL',
      chunks: 980,
      indexedDate: '2026-08-12',
    },
  ];

  const filteredDocs = documents.filter((d) => {
    const matchesCategory = activeCategory === 'All' || d.category === activeCategory;
    const matchesQuery =
      d.title.toLowerCase().includes(filter.toLowerCase()) ||
      d.id.toLowerCase().includes(filter.toLowerCase()) ||
      d.authority.toLowerCase().includes(filter.toLowerCase());
    return matchesCategory && matchesQuery;
  });

  return (
    <div className="min-h-screen w-full bg-[#EEF3E4] font-sans-body relative flex flex-col p-6 lg:p-12">
      {/* Header */}
      <header className="max-w-6xl w-full mx-auto flex items-center justify-between mb-8 relative z-20">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-xs font-semibold text-[#003E29] bg-white border border-[#C8D7C2] px-3.5 py-2 rounded-lg hover:bg-[#FAFDF6] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Research Dashboard</span>
        </Link>

        <HeaderUserProfile />
      </header>

      {/* Main Knowledge Base Content */}
      <main className="max-w-6xl w-full mx-auto bg-white border border-[#C8D7C2] rounded-2xl p-8 lg:p-10 shadow-sm relative z-10 space-y-6">
        <div className="border-b border-[#C8D7C2]/80 pb-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 bg-[#EEF3E4] text-[#003E29] text-xs font-bold px-3 py-1 rounded-md mb-2">
              <Database className="w-3.5 h-3.5" />
              <span>Grounded Index Explorer</span>
            </div>
            <h1 className="font-serif-heading text-3xl lg:text-4xl font-bold text-[#003E29]">
              Grounded Knowledge Base & Corpus Explorer
            </h1>
            <p className="text-xs text-[#385246] mt-1">
              Inspect authoritative corpus documents, FAISS dense embeddings, and BM25 sparse keyword indices.
            </p>
          </div>
        </div>

        {/* Category Tabs & Search Bar */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          {/* Category Filter Pills */}
          <div className="flex flex-wrap gap-1.5">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                  activeCategory === cat
                    ? 'bg-[#003E29] text-white font-semibold'
                    : 'bg-[#EEF3E4] text-[#003E29] hover:bg-[#E3EBD7] border border-[#C8D7C2]'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div className="relative w-full md:w-72">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-[#385246]" />
            <input
              type="text"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="Search corpus index..."
              className="w-full bg-[#FAFDF6] border border-[#C8D7C2] rounded-lg pl-9 pr-3 py-2 text-xs text-[#003E29] placeholder-[#7C817A] focus:outline-none focus:border-[#003E29]"
            />
          </div>
        </div>

        {/* Document Table */}
        <div className="border border-[#C8D7C2] rounded-xl overflow-hidden text-xs shadow-xs">
          <table className="w-full text-left">
            <thead className="bg-[#003E29] text-white font-bold">
              <tr>
                <th className="p-3.5">Source ID</th>
                <th className="p-3.5">Document Title / Authority</th>
                <th className="p-3.5">Category</th>
                <th className="p-3.5">Indexed Chunks</th>
                <th className="p-3.5">Last Index Date</th>
                <th className="p-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#C8D7C2]/60 text-[#1A2E26]">
              {filteredDocs.map((doc) => (
                <tr key={doc.id} className="hover:bg-[#FAFDF6]">
                  <td className="p-3.5 font-mono font-semibold text-[#003E29] bg-[#EEF3E4]/30">{doc.id}</td>
                  <td className="p-3.5 font-medium">
                    <div className="font-semibold text-[#003E29]">{doc.title}</div>
                    <div className="text-[11px] text-[#385246]">{doc.authority}</div>
                  </td>
                  <td className="p-3.5">
                    <span className="bg-emerald-50 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded border border-emerald-200">
                      {doc.category}
                    </span>
                  </td>
                  <td className="p-3.5 font-mono">{doc.chunks} chunks</td>
                  <td className="p-3.5 text-[#385246]">{doc.indexedDate}</td>
                  <td className="p-3.5 text-right">
                    <button
                      onClick={() => alert(`Inspecting chunks for: ${doc.id}`)}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-[#003E29] hover:underline cursor-pointer"
                    >
                      <FileText className="w-3.5 h-3.5 text-[#003E29]" />
                      <span>Inspect Chunks</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
