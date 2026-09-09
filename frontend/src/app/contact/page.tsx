'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  ChevronRight,
  Leaf,
  Globe,
  Bell,
  Settings,
  MessageSquare,
  BookOpen,
  Users,
  Send,
  Lock,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import Sidebar from '@/components/Sidebar';
import HeaderUserProfile from '@/components/HeaderUserProfile';
import BotanicalBackground from '@/components/BotanicalBackground';
import { useAuth } from '@/context/AuthContext';
import { Conversation, listConversations } from '@/lib/api';

export default function ContactPage() {
  const { user, profile } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);

  // Form Fields State
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');

  // Validation & Feedback States
  const [nameError, setNameError] = useState('');
  const [emailError, setEmailError] = useState('');
  const [subjectError, setSubjectError] = useState('');
  const [messageError, setMessageError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toastMessage, setToastMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Sync authenticated user info into form defaults
  useEffect(() => {
    if (profile?.fullName) {
      setName(profile.fullName);
    } else if (user?.email) {
      setName(user.email.split('@')[0]);
    }

    if (profile?.email) {
      setEmail(profile.email);
    } else if (user?.email) {
      setEmail(user.email);
    }
  }, [profile, user]);

  // Load conversations for sidebar
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

  const validateForm = () => {
    let isValid = true;
    setNameError('');
    setEmailError('');
    setSubjectError('');
    setMessageError('');
    setToastMessage(null);

    if (!name.trim()) {
      setNameError('Please enter your full name.');
      isValid = false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.trim()) {
      setEmailError('Please enter your email address.');
      isValid = false;
    } else if (!emailRegex.test(email.trim())) {
      setEmailError('Please enter a valid email address.');
      isValid = false;
    }

    if (!subject || subject === 'Select a subject') {
      setSubjectError('Please select a support subject.');
      isValid = false;
    }

    if (!message.trim()) {
      setMessageError('Please enter your message.');
      isValid = false;
    } else if (message.trim().length > 1000) {
      setMessageError('Message must be 1000 characters or less.');
      isValid = false;
    }

    return isValid;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsSubmitting(true);

    // Prepare payload for future API/Supabase submission
    const _payload = {
      user_id: user?.id || 'anonymous',
      name: name.trim(),
      email: email.trim(),
      subject: subject,
      message: message.trim(),
      created_at: new Date().toISOString(),
    };

    setTimeout(() => {
      setIsSubmitting(false);
      setToastMessage({
        type: 'success',
        text: 'Message ready to send. Your support request has been validated successfully. Backend submission will be connected shortly.',
      });
      setSubject('');
      setMessage('');
    }, 400);
  };

  const supportAreas = [
    {
      title: 'Technical Support',
      description: "Facing issues while using the platform? We're here to help.",
      icon: Settings,
    },
    {
      title: 'Platform Feedback',
      description: 'Share your suggestions to help us improve IP-SAKTI Sahayak.',
      icon: MessageSquare,
    },
    {
      title: 'Research Assistance',
      description: 'Need guidance on traditional knowledge, IP, AYUSH or ABS related queries?',
      icon: BookOpen,
    },
    {
      title: 'General Enquiries',
      description: 'Have a question about the project, features or collaboration? Reach out to us.',
      icon: Users,
    },
  ];

  return (
    <div className="min-h-screen w-full bg-[#EEF3E4] font-sans-body relative flex">
      {/* 1. SIDEBAR */}
      <Sidebar
        conversations={conversations}
        activeConversationId={null}
        onSelectConversation={(id) => (window.location.href = `/?conv=${id}`)}
        onNewChat={() => (window.location.href = '/')}
        onDeleteConversation={(id) => setConversations((prev) => prev.filter((c) => c.id !== id))}
        onLogout={() => (window.location.href = '/login')}
      />

      {/* 2. MAIN APPLICATION CONTENT */}
      <main className="flex-1 lg:ml-[270px] min-h-screen flex flex-col p-6 lg:p-10 relative z-10 overflow-y-auto space-y-6">
        <BotanicalBackground />

        {/* TOP APPLICATION BAR */}
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

            {/* Dynamic User Profile */}
            <HeaderUserProfile />
          </div>
        </header>

        {/* BREADCRUMB */}
        <nav className="flex items-center gap-1.5 text-xs text-[#385246] font-medium relative z-10 -mt-2">
          <Link href="/" className="hover:text-[#003E29] hover:underline transition-colors">
            Home
          </Link>
          <ChevronRight className="w-3 h-3 text-[#7B9F8E]" />
          <span className="text-[#003E29] font-bold">Contact Support</span>
        </nav>

        {/* HERO SECTION */}
        <div className="flex flex-wrap items-end justify-between gap-4 relative z-10 pt-1">
          <div>
            <h1 className="font-serif-heading text-3xl lg:text-4xl font-bold text-[#003E29] tracking-tight">
              Contact Support
            </h1>
            <p className="text-xs lg:text-sm text-[#4A6357] mt-1 font-medium max-w-xl">
              We're here to help with your questions, feedback, and technical concerns.
            </p>
          </div>

          <div className="text-[10px] font-bold tracking-widest text-[#003E29] uppercase px-3 py-1 bg-white/70 border border-[#C8D7C2] rounded-full shadow-xs">
            PEOPLE · KNOWLEDGE · NATURE · BHARAT
          </div>
        </div>

        {/* TOAST / VALIDATION NOTIFICATION */}
        {toastMessage && (
          <div
            className={`border rounded-xl p-3.5 text-xs font-semibold flex items-center gap-2.5 shadow-xs transition-all animate-in fade-in duration-200 relative z-20 ${
              toastMessage.type === 'success'
                ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
                : 'bg-rose-50 border-rose-300 text-rose-900'
            }`}
          >
            {toastMessage.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            )}
            <span>{toastMessage.text}</span>
          </div>
        )}

        {/* MAIN CONTENT — TWO COLUMNS (LEFT 42% / RIGHT 58%) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 relative z-10 items-start">
          {/* LEFT CARD — IP-SAKTI SAHAYAK SUPPORT INFO (42% -> 5 COLS) */}
          <div className="lg:col-span-5 bg-white border border-[#C8D7C2] rounded-2xl p-6 shadow-xs space-y-6">
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-[#EEF3E4] border border-[#C8D7C2] flex items-center justify-center text-[#003E29] shrink-0">
                <Leaf className="w-5 h-5" />
              </div>
              <div>
                <h2 className="font-serif-heading font-bold text-xl text-[#003E29]">
                  IP-SAKTI Sahayak
                </h2>
                <div className="text-xs text-[#4A6357] font-medium mt-0.5">
                  Traditional Knowledge · Intellectual Property · AYUSH
                </div>
              </div>
              <p className="text-xs text-[#385246] leading-relaxed">
                For any queries, suggestions, technical issues or collaboration opportunities, please reach out to our team through the form. We value your feedback and will get back to you at the earliest.
              </p>
            </div>

            {/* SUPPORT AREAS */}
            <div className="space-y-4 pt-2 border-t border-[#C8D7C2]/60">
              <h3 className="font-serif-heading font-bold text-sm text-[#003E29]">
                Support Areas
              </h3>

              <div className="space-y-3.5">
                {supportAreas.map((area, idx) => {
                  const Icon = area.icon;
                  return (
                    <div key={idx} className="flex items-start gap-3">
                      <div className="w-9 h-9 rounded-full bg-[#EEF3E4] border border-[#C8D7C2] text-[#003E29] flex items-center justify-center shrink-0 mt-0.5">
                        <Icon className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="font-serif-heading font-bold text-xs text-[#003E29]">
                          {area.title}
                        </div>
                        <div className="text-[11px] text-[#4A6357] leading-snug mt-0.5">
                          {area.description}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* RIGHT CARD — SEND A MESSAGE FORM (58% -> 7 COLS) */}
          <div className="lg:col-span-7 bg-white border border-[#C8D7C2] rounded-2xl p-6 lg:p-8 shadow-xs space-y-5">
            <div>
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-[#003E29] text-white flex items-center justify-center shrink-0">
                  <Send className="w-4 h-4 text-[#A1C9B6]" />
                </div>
                <h2 className="font-serif-heading font-bold text-xl text-[#003E29]">
                  Send a Message
                </h2>
              </div>
              <p className="text-xs text-[#4A6357] font-medium mt-1">
                Fill in the form below and our team will get back to you soon.
              </p>
            </div>

            <form onSubmit={handleSubmit} noValidate className="space-y-4 text-xs">
              {/* Your Name */}
              <div>
                <label className="block font-bold text-[#003E29] mb-1.5">
                  Your Name <span className="text-rose-600">*</span>
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    if (nameError) setNameError('');
                  }}
                  placeholder="Enter your name"
                  className={`w-full bg-white border rounded-lg px-3.5 py-2.5 text-xs text-[#003E29] focus:outline-none focus:border-[#003E29] focus:ring-1 focus:ring-[#003E29] transition-all shadow-xs font-medium ${
                    nameError ? 'border-rose-400 bg-rose-50/20' : 'border-[#C8D7C2]'
                  }`}
                />
                {nameError && (
                  <p className="text-[11px] text-rose-600 font-medium mt-1">{nameError}</p>
                )}
              </div>

              {/* Your Email */}
              <div>
                <label className="block font-bold text-[#003E29] mb-1.5">
                  Your Email <span className="text-rose-600">*</span>
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (emailError) setEmailError('');
                  }}
                  placeholder="Enter your email address"
                  className={`w-full bg-white border rounded-lg px-3.5 py-2.5 text-xs text-[#003E29] focus:outline-none focus:border-[#003E29] focus:ring-1 focus:ring-[#003E29] transition-all shadow-xs font-medium ${
                    emailError ? 'border-rose-400 bg-rose-50/20' : 'border-[#C8D7C2]'
                  }`}
                />
                {emailError && (
                  <p className="text-[11px] text-rose-600 font-medium mt-1">{emailError}</p>
                )}
              </div>

              {/* Subject */}
              <div>
                <label className="block font-bold text-[#003E29] mb-1.5">
                  Subject <span className="text-rose-600">*</span>
                </label>
                <select
                  value={subject}
                  onChange={(e) => {
                    setSubject(e.target.value);
                    if (subjectError) setSubjectError('');
                  }}
                  className={`w-full bg-white border rounded-lg px-3.5 py-2.5 text-xs text-[#003E29] focus:outline-none focus:border-[#003E29] focus:ring-1 focus:ring-[#003E29] transition-all shadow-xs font-medium cursor-pointer ${
                    subjectError ? 'border-rose-400 bg-rose-50/20' : 'border-[#C8D7C2]'
                  }`}
                >
                  <option value="">Select a subject</option>
                  <option value="Technical Support">Technical Support</option>
                  <option value="Platform Feedback">Platform Feedback</option>
                  <option value="Research Assistance">Research Assistance</option>
                  <option value="General Enquiry">General Enquiry</option>
                  <option value="Collaboration">Collaboration</option>
                  <option value="Other">Other</option>
                </select>
                {subjectError && (
                  <p className="text-[11px] text-rose-600 font-medium mt-1">{subjectError}</p>
                )}
              </div>

              {/* Message */}
              <div>
                <label className="block font-bold text-[#003E29] mb-1.5">
                  Message <span className="text-rose-600">*</span>
                </label>
                <textarea
                  value={message}
                  onChange={(e) => {
                    setMessage(e.target.value.slice(0, 1000));
                    if (messageError) setMessageError('');
                  }}
                  placeholder="Type your message here..."
                  rows={4}
                  className={`w-full bg-white border rounded-lg p-3 text-xs text-[#003E29] focus:outline-none focus:border-[#003E29] focus:ring-1 focus:ring-[#003E29] transition-all shadow-xs resize-none font-medium ${
                    messageError ? 'border-rose-400 bg-rose-50/20' : 'border-[#C8D7C2]'
                  }`}
                />
                <div className="flex items-center justify-between mt-1 text-[11px]">
                  {messageError ? (
                    <p className="text-rose-600 font-medium">{messageError}</p>
                  ) : (
                    <span />
                  )}
                  <span className="text-[#4A6357] font-medium ml-auto">
                    {message.length} / 1000
                  </span>
                </div>
              </div>

              {/* Send Button */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full sm:w-auto flex items-center justify-center gap-2 bg-[#003E29] hover:bg-[#044D34] text-white font-semibold py-3 px-8 rounded-lg text-xs transition-all shadow-xs active:scale-[0.99] cursor-pointer"
                >
                  <Send className="w-4 h-4 text-[#A1C9B6]" />
                  <span>{isSubmitting ? 'Validating...' : 'Send Message'}</span>
                </button>
              </div>

              {/* Privacy Note */}
              <div className="flex items-center gap-1.5 text-[11px] text-[#4A6357] font-medium pt-1">
                <Lock className="w-3.5 h-3.5 text-[#003E29] shrink-0" />
                <span>Your information is kept confidential and will only be used for support purposes.</span>
              </div>
            </form>
          </div>
        </div>

        {/* GITHUB OPEN SOURCE SECTION */}
        <section className="bg-white border border-[#C8D7C2] rounded-2xl p-6 shadow-xs flex flex-wrap items-center justify-between gap-4 relative z-10">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-[#003E29] text-white flex items-center justify-center shrink-0 border border-[#195941] shadow-xs">
              <svg className="w-6 h-6 fill-current text-[#E2EFE9]" viewBox="0 0 24 24">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
              </svg>
            </div>
            <div>
              <h3 className="font-serif-heading font-bold text-base text-[#003E29]">
                Connect with IP-SAKTI on GitHub
              </h3>
              <p className="text-xs text-[#385246] max-w-xl mt-0.5 leading-relaxed">
                Explore our open-source project, development work, and SIH 2026 implementation. You can also reach our team through GitHub issues and discussions.
              </p>
            </div>
          </div>

          <a
            href="https://github.com/IP-SAKTI/IP-SAKTI"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 bg-[#003E29] hover:bg-[#044D34] text-white font-semibold py-2.5 px-5 rounded-lg text-xs transition-all shadow-xs active:scale-95 shrink-0"
          >
            <span>Visit IP-SAKTI GitHub</span>
            <ExternalLink className="w-3.5 h-3.5 text-[#A1C9B6]" />
          </a>
        </section>

        {/* CLOSING MISSION STATEMENT & FOOTER */}
        <footer className="w-full pt-6 pb-4 border-t border-[#C8D7C2]/60 text-center relative z-10 space-y-2">
          <div className="font-serif-heading text-sm font-bold text-[#003E29] italic">
            "Preserving knowledge. Enabling innovation. For a healthier, stronger Bharat."
          </div>

          <div className="text-[10px] font-bold tracking-widest text-[#003E29] uppercase">
            PEOPLE &nbsp;|&nbsp; KNOWLEDGE &nbsp;|&nbsp; NATURE &nbsp;|&nbsp; BHARAT
          </div>
        </footer>
      </main>
    </div>
  );
}
