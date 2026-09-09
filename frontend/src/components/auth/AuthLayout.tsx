'use client';

import React from 'react';
import BrandHeader from './BrandHeader';
import InitiativeCarousel from './InitiativeCarousel';
import MissionFooter from './MissionFooter';

interface AuthLayoutProps {
  children: React.ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen w-full flex flex-col md:flex-row relative font-sans-body bg-[#FAF8F1] overflow-x-hidden select-none">
      {/* Corner Botanical Line-Art Accent */}
      <svg
        className="absolute top-0 left-0 w-32 h-32 text-[#064E3B] opacity-15 pointer-events-none z-0"
        viewBox="0 0 100 100"
        fill="currentColor"
      >
        <path d="M0,0 Q50,0 30,50 Q10,100 0,100 Z" />
      </svg>

      {/* Thin Vertical Split Divider */}
      <div className="hidden md:block absolute top-0 bottom-0 left-[64%] w-[1px] bg-[#064E3B]/10 z-10 pointer-events-none" />

      {/* LEFT SIDE — ~64% Width */}
      <div className="w-full md:w-[64%] p-5 md:p-8 lg:p-10 flex flex-col justify-between relative z-10 bg-[#FAF8F1] min-h-screen">
        <div className="space-y-4 max-w-3xl">
          {/* 1. Brand Header */}
          <BrandHeader />

          {/* 2. Main Headline (Tightened Spacing & Refined Desktop Size) */}
          <div className="pt-1">
            <h1 className="font-serif-heading text-3xl sm:text-4xl lg:text-[2.6rem] font-bold text-[#064E3B] leading-[1.15] tracking-tight">
              Rooted in Bharat. Guided by Knowledge.
            </h1>
          </div>

          {/* 3. Description (Tightened Gap) */}
          <p className="text-xs sm:text-sm text-[#385246] leading-relaxed max-w-2xl font-sans-body">
            AI-powered research for patent prior art, AYUSH regulatory compliance, and Access & Benefit Sharing — grounded in trusted government sources.
          </p>

          {/* 4. Single Main Carousel (Compact Height ~265px, Fits Cleanly in Viewport) */}
          <div className="pt-2">
            <InitiativeCarousel />
          </div>

          {/* 5. Mission Statement & Indian Heritage Architecture Silhouette */}
          <div className="pt-4">
            <MissionFooter />
          </div>
        </div>
      </div>

      {/* RIGHT SIDE — ~36% Width Deep Forest Green Auth Panel (Positioned UPWARD) */}
      <div className="w-full md:w-[36%] bg-[#02281A] p-5 md:pt-8 md:px-8 lg:pt-10 lg:px-10 flex flex-col justify-between relative z-10 min-h-screen">
        {/* Top-Right Metadata Label */}
        <div className="text-right text-[9px] font-bold tracking-widest text-[#82A997] uppercase space-y-0.5 pb-2">
          <div>TRADITION</div>
          <div>RESEARCH</div>
          <div>REGULATION</div>
          <div>INNOVATION</div>
          <div className="text-emerald-400">A STRONGER BHARAT</div>
        </div>

        {/* Login / Register Card (Moved UPWARD with controlled top spacing) */}
        <div className="w-full max-w-[410px] mx-auto bg-[#032619]/95 border border-[#14533C]/60 rounded-2xl p-6 lg:p-7 shadow-2xl space-y-5 my-auto md:my-0 md:mt-2">
          {children}
        </div>

        {/* Bottom-Right Watermark */}
        <div className="pt-4 pb-2 text-right text-[10px] text-[#82A997] font-serif-heading italic flex items-center justify-end gap-1.5 mt-auto">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Knowledge for People. Nature. Bharat.</span>
        </div>
      </div>
    </div>
  );
}
