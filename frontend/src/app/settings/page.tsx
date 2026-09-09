'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { User, Save, Camera, CheckCircle2, AlertCircle, Leaf, Globe, Bell } from 'lucide-react';
import Sidebar from '@/components/Sidebar';
import HeaderUserProfile from '@/components/HeaderUserProfile';
import BotanicalBackground from '@/components/BotanicalBackground';
import { Conversation, listConversations } from '@/lib/api';

import { useAuth } from '@/context/AuthContext';

export default function SettingsPage() {
  const { user, profile: authProfile, updateProfile } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);

  // Profile Form States
  const [fullName, setFullName] = useState(authProfile?.fullName || 'User');
  const [email, setEmail] = useState(authProfile?.email || user?.email || '');
  const [organization, setOrganization] = useState(authProfile?.organization || 'IP-SAKTI');
  const [role, setRole] = useState(authProfile?.role || 'Researcher');
  const [bio, setBio] = useState(authProfile?.bio || '');
  const [avatarUrl, setAvatarUrl] = useState<string>(authProfile?.avatarUrl || '');

  // UI Feedback States
  const [isSaving, setIsSaving] = useState(false);
  const [toastMessage, setToastMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Sync profile when auth state resolves
  useEffect(() => {
    if (authProfile) {
      setFullName(authProfile.fullName);
      setEmail(authProfile.email || user?.email || '');
      setOrganization(authProfile.organization || 'IP-SAKTI');
      setRole(authProfile.role || 'Researcher');
      setBio(authProfile.bio || '');
      setAvatarUrl(authProfile.avatarUrl || '');
    }
  }, [authProfile, user]);

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

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setToastMessage(null);

    try {
      await updateProfile({
        fullName,
        email,
        organization,
        role,
        bio,
        avatarUrl,
      });
      setToastMessage({ type: 'success', text: 'Profile updated successfully.' });
    } catch (err) {
      setToastMessage({ type: 'error', text: 'Unable to update your profile. Please try again.' });
    } finally {
      setIsSaving(false);
      setTimeout(() => setToastMessage(null), 4000);
    }
  };

  const handlePhotoClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          const newAvatar = event.target.result as string;
          setAvatarUrl(newAvatar);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const avatarInitial = fullName.trim() ? fullName.trim().charAt(0).toUpperCase() : 'M';

  return (
    <div className="min-h-screen w-full bg-[#EEF3E4] font-sans-body relative flex">
      {/* 1. SIDEBAR (MATCHES APPLICATION SHELL) */}
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewChat={() => (window.location.href = '/')}
        onDeleteConversation={handleDeleteConversation}
        onLogout={() => (window.location.href = '/login')}
      />

      {/* 2. MAIN APPLICATION CONTENT AREA */}
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

            {/* User Profile */}
            <HeaderUserProfile
              userName={fullName}
              userEmail={email}
              onLogout={() => (window.location.href = '/login')}
            />
          </div>
        </header>

        {/* SETTINGS PAGE HEADER & MOTTO */}
        <div className="flex flex-wrap items-end justify-between gap-4 relative z-10 pt-2">
          <div>
            <h1 className="font-serif-heading text-3xl lg:text-4xl font-bold text-[#003E29] tracking-tight">
              Settings
            </h1>
            <p className="text-xs lg:text-sm text-[#4A6357] mt-1 font-medium">
              Manage your account, preferences, and application settings.
            </p>
          </div>

          <div className="text-xs text-[#003E29] font-serif-heading italic font-semibold flex items-center gap-1.5">
            <Leaf className="w-4 h-4 text-[#003E29]" />
            <span>Secure · Personalized · For a Greater Impact</span>
          </div>
        </div>

        {/* TOAST NOTIFICATION */}
        {toastMessage && (
          <div
            className={`border rounded-xl p-3.5 text-xs font-semibold flex items-center gap-2 shadow-xs transition-all animate-in fade-in duration-200 ${
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

        {/* ACCOUNT INFORMATION CARD */}
        <form onSubmit={handleSave} className="space-y-6 relative z-10 max-w-5xl">
          <div className="bg-white border border-[#C8D7C2] rounded-2xl p-6 lg:p-8 shadow-xs space-y-6">
            {/* Card Header Row */}
            <div className="flex items-center justify-between gap-4 pb-4 border-b border-[#C8D7C2]/60">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-[#EEF3E4] border border-[#C8D7C2] flex items-center justify-center text-[#003E29] shrink-0">
                  <User className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="font-serif-heading text-xl font-bold text-[#003E29]">
                    Account Information
                  </h2>
                  <p className="text-xs text-[#4A6357] mt-0.5 font-medium">
                    Update your personal details and account information.
                  </p>
                </div>
              </div>

              {/* Save Changes Button */}
              <button
                type="submit"
                disabled={isSaving}
                className="flex items-center gap-2 bg-[#003E29] hover:bg-[#044D34] text-white font-semibold py-2.5 px-5 rounded-lg text-xs transition-all shadow-xs active:scale-95 cursor-pointer shrink-0"
              >
                <Save className="w-4 h-4" />
                <span>{isSaving ? 'Saving...' : 'Save Changes'}</span>
              </button>
            </div>

            {/* Profile Summary & Photo Row */}
            <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-[#C8D7C2]/60">
              <div className="flex items-center gap-4">
                {/* Circular Avatar */}
                <div className="relative w-16 h-16 rounded-full bg-[#E2EFE9] border-2 border-[#A1C9B6] text-[#003E29] font-bold text-2xl flex items-center justify-center overflow-hidden shrink-0 shadow-xs">
                  {avatarUrl ? (
                    <img src={avatarUrl} alt="User Avatar" className="w-full h-full object-cover" />
                  ) : (
                    <span>{avatarInitial}</span>
                  )}
                  <div className="absolute bottom-0 right-0 bg-[#003E29] text-white p-1 rounded-full border border-white">
                    <Camera className="w-3 h-3" />
                  </div>
                </div>

                {/* User Info Details */}
                <div>
                  <h3 className="font-serif-heading font-bold text-lg text-[#003E29] leading-tight">
                    {fullName || 'User'}
                  </h3>
                  <div className="text-xs text-[#4A6357] font-medium mt-0.5">{email}</div>
                  <div className="text-xs text-[#385246] font-medium mt-1 inline-block bg-[#EEF3E4] border border-[#C8D7C2] px-2 py-0.5 rounded text-[11px]">
                    {organization} · {role}
                  </div>
                </div>
              </div>

              {/* Change Photo Button */}
              <div>
                <button
                  type="button"
                  onClick={handlePhotoClick}
                  className="flex items-center gap-2 bg-white hover:bg-[#EEF3E4] border border-[#C8D7C2] text-[#003E29] font-semibold py-2 px-4 rounded-lg text-xs transition-colors shadow-xs cursor-pointer"
                >
                  <Camera className="w-4 h-4 text-[#003E29]" />
                  <span>Change Photo</span>
                </button>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept="image/*"
                  className="hidden"
                />
              </div>
            </div>

            {/* Form Fields Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-xs">
              {/* Full Name */}
              <div>
                <label className="block font-bold text-[#003E29] mb-1.5">Full Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Enter your full name"
                  className="w-full bg-white border border-[#C8D7C2] rounded-lg px-3.5 py-2.5 text-xs text-[#003E29] focus:outline-none focus:border-[#003E29] focus:ring-1 focus:ring-[#003E29] transition-all shadow-xs font-medium"
                />
              </div>

              {/* Email Address (Read-Only) */}
              <div>
                <label className="block font-bold text-[#003E29] mb-1.5">Email Address</label>
                <input
                  type="email"
                  value={email}
                  readOnly
                  disabled
                  className="w-full bg-[#EEF3E4]/60 border border-[#C8D7C2] rounded-lg px-3.5 py-2.5 text-xs text-[#4A6357] font-medium shadow-xs cursor-not-allowed"
                />
              </div>

              {/* Organization */}
              <div>
                <label className="block font-bold text-[#003E29] mb-1.5">Organization</label>
                <input
                  type="text"
                  value={organization}
                  onChange={(e) => setOrganization(e.target.value)}
                  placeholder="IP-SAKTI"
                  className="w-full bg-white border border-[#C8D7C2] rounded-lg px-3.5 py-2.5 text-xs text-[#003E29] focus:outline-none focus:border-[#003E29] focus:ring-1 focus:ring-[#003E29] transition-all shadow-xs font-medium"
                />
              </div>

              {/* Role */}
              <div>
                <label className="block font-bold text-[#003E29] mb-1.5">Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full bg-white border border-[#C8D7C2] rounded-lg px-3.5 py-2.5 text-xs text-[#003E29] focus:outline-none focus:border-[#003E29] focus:ring-1 focus:ring-[#003E29] transition-all shadow-xs font-medium cursor-pointer"
                >
                  <option value="Researcher">Researcher</option>
                  <option value="Legal Expert">Legal Expert</option>
                  <option value="AYUSH Specialist">AYUSH Specialist</option>
                  <option value="IP Officer">IP Officer</option>
                  <option value="Policy Analyst">Policy Analyst</option>
                  <option value="User">User</option>
                </select>
              </div>

              {/* Bio Field (Full Width) */}
              <div className="md:col-span-2">
                <label className="block font-bold text-[#003E29] mb-1.5">Bio (Optional)</label>
                <textarea
                  value={bio}
                  onChange={(e) => setBio(e.target.value.slice(0, 300))}
                  placeholder="Add a short bio about yourself..."
                  rows={4}
                  className="w-full bg-white border border-[#C8D7C2] rounded-lg p-3 text-xs text-[#003E29] focus:outline-none focus:border-[#003E29] focus:ring-1 focus:ring-[#003E29] transition-all shadow-xs resize-none font-medium"
                />
                <div className="text-[11px] text-[#4A6357] text-right font-medium mt-1">
                  {bio.length} / 300
                </div>
              </div>
            </div>
          </div>
        </form>
      </main>
    </div>
  );
}
