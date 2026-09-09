'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  ChevronRight,
  BookOpen,
  ShieldCheck,
  Sparkles,
  Users,
  Eye,
  Target,
  Bell,
  Globe,
  Award,
  CheckCircle2,
  Cpu,
  Layers,
  Search,
  MessageSquare,
  Building2,
} from 'lucide-react';
import Sidebar from '@/components/Sidebar';
import HeaderUserProfile from '@/components/HeaderUserProfile';
import BotanicalBackground from '@/components/BotanicalBackground';
import { useAuth } from '@/context/AuthContext';
import { Conversation, listConversations } from '@/lib/api';

export default function AboutPage() {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);

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

  const handleSelectConversation = (id: string) => {
    window.location.href = `/?conv=${id}`;
  };

  const handleDeleteConversation = (id: string) => {
    setConversations((prev) => prev.filter((c) => c.id !== id));
  };

  const domains = [
    {
      title: 'Traditional Knowledge',
      description: "Explore India's knowledge heritage and relevant references.",
      icon: BookOpen,
    },
    {
      title: 'Intellectual Property',
      description: 'Understand patentability, prior art and related IP concepts.',
      icon: ShieldCheck,
    },
    {
      title: 'AYUSH Regulatory',
      description: 'Navigate regulatory requirements for AYUSH systems and formulations.',
      icon: Sparkles,
    },
    {
      title: 'Access & Benefit Sharing',
      description: 'Learn about ABS obligations and responsible use of biological resources.',
      icon: Users,
    },
  ];

  const steps = [
    {
      num: '1',
      title: 'Ask Your Question',
      desc: 'Type your query in natural language.',
    },
    {
      num: '2',
      title: 'Understand Intent',
      desc: 'The system analyses your query and identifies domain & entities.',
    },
    {
      num: '3',
      title: 'Retrieve Information',
      desc: 'Relevant information is retrieved from trusted public sources.',
    },
    {
      num: '4',
      title: 'AI-Assisted Analysis',
      desc: 'Information is structured and summarised with source references.',
    },
    {
      num: '5',
      title: 'Get Your Answer',
      desc: 'Receive a clear response with citations and confidence indicators.',
    },
  ];

  const team = [
    {
      name: 'Manaswitha Chowdary',
      role: 'Team Leader',
      initials: 'MC',
      responsibilities: ['UI/UX Design', 'Frontend Development', 'Project Coordination'],
    },
    {
      name: 'Johney Rejithaliah',
      role: 'AI/ML & Backend',
      initials: 'JR',
      responsibilities: ['Model Integration', 'Backend APIs', 'System Architecture'],
    },
    {
      name: 'Devaj Ragesh',
      role: 'Research & Knowledge Integration',
      initials: 'DR',
      responsibilities: ['Traditional Knowledge Research', 'Data Curation', 'Source Validation'],
    },
    {
      name: 'Preethi',
      role: 'Content & Documentation',
      initials: 'P',
      responsibilities: ['Content Writing', 'Domain Research', 'Technical Documentation'],
    },
    {
      name: 'Lokesh',
      role: 'Testing, Deployment & DevOps',
      initials: 'L',
      responsibilities: ['System Testing', 'Deployment', 'Performance Optimization'],
    },
    {
      name: 'Satyakam Tripathy',
      role: 'Strategy & Outreach',
      initials: 'ST',
      responsibilities: ['Impact Analysis', 'Presentation Design', 'Stakeholder Engagement'],
    },
  ];

  return (
    <div className="min-h-screen w-full bg-[#EEF3E4] font-sans-body relative flex">
      {/* Fixed Sidebar */}
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewChat={() => (window.location.href = '/')}
        onDeleteConversation={handleDeleteConversation}
        onOpenSettings={() => alert('Account Settings')}
        onLogout={() => (window.location.href = '/login')}
      />

      {/* Main Scrollable Content */}
      <main className="flex-1 lg:ml-[270px] min-h-screen flex flex-col p-6 lg:p-10 relative z-10 overflow-y-auto space-y-8">
        <BotanicalBackground />

        {/* 1. TOP APPLICATION BAR */}
        <header className="w-full flex flex-wrap items-center justify-between gap-4 relative z-20">
          <div className="text-xs font-semibold text-[#003E29] bg-white border border-[#C8D7C2] px-3.5 py-1.5 rounded-full shadow-xs">
            IP-SAKTI Sahayak · Enterprise AI Research Platform
          </div>

          <div className="flex items-center gap-3">
            {/* Language Selector */}
            <div className="flex items-center gap-1 bg-[#FAFDF6] border border-[#C8D7C2] px-3 py-1.5 rounded-lg text-xs font-medium text-[#003E29]">
              <Globe className="w-3.5 h-3.5 text-[#003E29]" />
              <span>English</span>
              <span className="text-[10px] text-[#4A6357]">▼</span>
            </div>

            {/* Notification Icon */}
            <button
              className="p-1.5 bg-[#FAFDF6] border border-[#C8D7C2] rounded-lg text-[#003E29] hover:bg-[#F4FAF0] transition-colors cursor-pointer"
              title="Notifications"
            >
              <Bell className="w-4 h-4" />
            </button>

            <HeaderUserProfile />
          </div>
        </header>

        {/* 2. BREADCRUMB */}
        <nav className="flex items-center gap-1.5 text-xs text-[#385246] font-medium relative z-10 -mt-2">
          <Link href="/" className="hover:text-[#003E29] hover:underline transition-colors">
            Home
          </Link>
          <ChevronRight className="w-3 h-3 text-[#7B9F8E]" />
          <span className="text-[#003E29] font-bold">About</span>
        </nav>

        {/* 3. MAIN ABOUT HEADER & HERO */}
        <section className="bg-white border border-[#C8D7C2] rounded-2xl p-6 lg:p-8 shadow-xs relative z-10 flex flex-col md:flex-row items-stretch justify-between gap-6">
          <div className="max-w-2xl space-y-3">
            <div>
              <h1 className="font-serif-heading text-3xl lg:text-4xl font-bold text-[#003E29] tracking-tight">
                About IP-SAKTI Sahayak
              </h1>
              <div className="font-serif-heading italic text-xs lg:text-sm text-[#385246] font-semibold mt-1">
                Rooted in Bharat. Guided by Knowledge.
              </div>
            </div>

            <p className="text-xs lg:text-sm text-[#263A35] leading-relaxed font-sans-body">
              IP-SAKTI Sahayak is an AI-powered research and decision-support platform designed to make India's Traditional Knowledge, Intellectual Property, AYUSH regulatory pathways, and Access & Benefit Sharing (ABS) easier to explore, understand and navigate — using trusted and publicly available sources.
            </p>

            <div className="pt-2 flex items-center gap-2 text-[11px] font-semibold text-[#003E29]">
              <span className="bg-[#EEF3E4] px-2.5 py-1 rounded border border-[#C8D7C2]">
                Multilingual AI Engine
              </span>
              <span className="bg-[#EEF3E4] px-2.5 py-1 rounded border border-[#C8D7C2]">
                Authoritative Grounding
              </span>
              <span className="bg-[#EEF3E4] px-2.5 py-1 rounded border border-[#C8D7C2]">
                Decision Support System
              </span>
            </div>
          </div>

          {/* Right Side Institutional Heritage Badge */}
          <div className="w-full md:w-64 bg-[#FAFDF6] border border-[#C8D7C2] rounded-xl p-5 flex flex-col justify-between shrink-0">
            <div className="space-y-2">
              <div className="w-8 h-8 rounded-lg bg-[#003E29] text-white flex items-center justify-center font-bold text-xs shadow-xs">
                <Building2 className="w-4 h-4 text-[#A1C9B6]" />
              </div>
              <div className="font-serif-heading font-bold text-sm text-[#003E29]">
                National Knowledge &amp; Research Portal
              </div>
              <div className="text-[11px] text-[#4A6357] leading-tight">
                Grounded in TKDL, Indian Patent Office, Ministry of AYUSH, and NBA regulatory archives.
              </div>
            </div>

            <div className="pt-3 border-t border-[#C8D7C2]/60 text-[10px] font-bold text-[#003E29] uppercase tracking-wider">
              GOVERNMENT OF INDIA INITIATIVE
            </div>
          </div>
        </section>

        {/* 4. VISION + MISSION */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-5 relative z-10">
          {/* Vision Card */}
          <div className="bg-white border border-[#C8D7C2] rounded-xl p-6 shadow-xs space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[#003E29] flex items-center justify-center text-white shrink-0">
                <Eye className="w-4.5 h-4.5 text-[#A1C9B6]" />
              </div>
              <h2 className="font-serif-heading text-xl font-bold text-[#003E29]">
                Our Vision
              </h2>
            </div>
            <p className="text-xs lg:text-sm text-[#263A35] leading-relaxed italic">
              "To empower researchers, innovators and policymakers with reliable, accessible and multilingual knowledge support for a healthier and more innovative India."
            </p>
          </div>

          {/* Mission Card */}
          <div className="bg-white border border-[#C8D7C2] rounded-xl p-6 shadow-xs space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[#003E29] flex items-center justify-center text-white shrink-0">
                <Target className="w-4.5 h-4.5 text-[#A1C9B6]" />
              </div>
              <h2 className="font-serif-heading text-xl font-bold text-[#003E29]">
                Our Mission
              </h2>
            </div>
            <p className="text-xs lg:text-sm text-[#263A35] leading-relaxed italic">
              "To bridge information gaps using AI and authoritative sources, and to promote responsible use of India's traditional knowledge."
            </p>
          </div>
        </section>

        {/* 5. KEY DOMAINS SUPPORTED */}
        <section className="space-y-4 relative z-10">
          <h2 className="font-serif-heading text-2xl font-bold text-[#003E29]">
            Key Domains IP-SAKTI Supports
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {domains.map((d, i) => {
              const Icon = d.icon;
              return (
                <div
                  key={i}
                  className="bg-white border border-[#C8D7C2] rounded-xl p-4 shadow-xs hover:border-[#003E29] transition-colors flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <div className="w-8 h-8 rounded-lg bg-[#EEF3E4] border border-[#C8D7C2] flex items-center justify-center text-[#003E29]">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="font-serif-heading font-bold text-sm text-[#003E29]">
                      {d.title}
                    </div>
                    <p className="text-xs text-[#385246] leading-relaxed">
                      {d.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* 6. HOW IP-SAKTI WORKS */}
        <section className="space-y-4 relative z-10">
          <h2 className="font-serif-heading text-2xl font-bold text-[#003E29]">
            How IP-SAKTI Works
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {steps.map((s, idx) => (
              <div
                key={idx}
                className="bg-white border border-[#C8D7C2] rounded-xl p-4 shadow-xs flex flex-col justify-between relative"
              >
                <div className="space-y-2">
                  <div className="w-7 h-7 rounded-full bg-[#003E29] text-white flex items-center justify-center font-bold text-xs">
                    {s.num}
                  </div>
                  <div className="font-serif-heading font-bold text-xs text-[#003E29] leading-snug">
                    {s.title}
                  </div>
                  <p className="text-[11px] text-[#385246] leading-relaxed">
                    {s.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* 7. OUR TEAM — SIH 2026 */}
        <section className="space-y-4 relative z-10">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-serif-heading text-2xl font-bold text-[#003E29]">
                Our Team — SIH 2026
              </h2>
              <p className="text-xs text-[#385246] font-serif-heading italic mt-0.5">
                Six minds. One mission. A stronger Bharat.
              </p>
            </div>

            <div className="flex items-center gap-1.5 bg-[#FAFDF6] border border-[#D8C7A2] px-3 py-1 rounded-full text-xs font-semibold text-[#8C6B28] shadow-xs">
              <Award className="w-3.5 h-3.5 text-[#8C6B28]" />
              <span>Student Innovation Hackathon 2026</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {team.map((t, idx) => (
              <div
                key={idx}
                className="bg-white border border-[#C8D7C2] rounded-xl p-3 shadow-xs flex flex-col justify-between hover:border-[#003E29] transition-colors"
              >
                <div>
                  <div className="w-8 h-8 rounded-full bg-[#003E29] text-white font-bold text-xs flex items-center justify-center shrink-0 border border-[#195941] mb-2">
                    {t.initials}
                  </div>
                  <div className="font-serif-heading font-bold text-xs text-[#003E29] leading-tight">
                    {t.name}
                  </div>
                  <div className="text-[11px] font-semibold text-[#385246] mt-0.5 leading-snug">
                    {t.role}
                  </div>
                </div>

                <div className="mt-2.5 pt-2 border-t border-[#C8D7C2]/60 space-y-0.5">
                  {t.responsibilities.map((resp, rIdx) => (
                    <div key={rIdx} className="text-[10px] text-[#4A6357] leading-tight flex items-start gap-1">
                      <span className="text-[#003E29] font-bold">•</span>
                      <span>{resp}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* 8. CLOSING MISSION STATEMENT & FOOTER */}
        <footer className="w-full pt-6 pb-4 border-t border-[#C8D7C2]/60 text-center relative z-10 space-y-2">
          <div className="font-serif-heading text-base font-bold text-[#003E29] italic">
            "Knowledge for a Healthier, Stronger Bharat."
          </div>

          <div className="text-[10px] font-bold tracking-widest text-[#003E29] uppercase">
            PEOPLE &nbsp;|&nbsp; KNOWLEDGE &nbsp;|&nbsp; NATURE &nbsp;|&nbsp; BHARAT
          </div>

          <div className="text-[11px] text-[#385246] font-medium pt-1">
            IP-SAKTI Sahayak · AI-Assisted Decision Support System for Traditional Knowledge &amp; IP
          </div>
        </footer>
      </main>
    </div>
  );
}
