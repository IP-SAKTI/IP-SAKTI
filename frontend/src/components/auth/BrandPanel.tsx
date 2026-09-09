'use client';

import React from 'react';
import { Leaf, Sparkles, ShieldCheck } from 'lucide-react';
import IpSaktiLogo from '../IpSaktiLogo';

export default function BrandPanel() {
  return (
    <div className="w-full md:w-1/2 p-8 md:p-12 lg:p-16 flex flex-col justify-between relative z-10 min-h-[500px] md:min-h-screen font-sans-body bg-[#FAF9F2]">
      {/* Centered Content Container */}
      <div className="max-w-[540px] w-full mx-auto space-y-6">
        {/* Brand Logo */}
        <div className="space-y-2">
          <IpSaktiLogo className="h-12 w-auto max-w-[260px] object-contain" />
        </div>

        {/* Refined Main Heading (Editorial Size: ~2.8rem, Clean Whitespace) */}
        <div className="pt-2">
          <h1 className="font-serif-heading text-3xl md:text-[2.75rem] font-bold text-[#064E3B] leading-[1.2] tracking-tight">
            Knowledge <br />
            for a healthier tomorrow.
          </h1>
        </div>

        {/* Supporting Description Paragraph */}
        <p className="text-xs md:text-sm text-[#385246] leading-relaxed max-w-md font-sans-body">
          Decision-support research for Traditional Knowledge, patent prior art, AYUSH regulatory compliance, and Access & Benefit Sharing — grounded in available source texts.
        </p>

        {/* Minimal Feature Metadata Row (No cards, No boxes) */}
        <div className="pt-4 border-t border-[#064E3B]/10 max-w-md">
          <div className="flex items-center gap-3 text-xs text-[#385246] font-medium">
            <div className="flex items-center gap-1.5 pr-3 border-r border-[#064E3B]/15">
              <Leaf className="w-3.5 h-3.5 text-[#064E3B]" />
              <span>Traditional Knowledge</span>
            </div>

            <div className="flex items-center gap-1.5 px-3 border-r border-[#064E3B]/15">
              <Sparkles className="w-3.5 h-3.5 text-[#064E3B]" />
              <span>AYUSH</span>
            </div>

            <div className="flex items-center gap-1.5 pl-1">
              <ShieldCheck className="w-3.5 h-3.5 text-[#064E3B]" />
              <span>Patents & Compliance</span>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Brand Statement (Simple italic text, NO green pill container) */}
      <div className="max-w-[540px] w-full mx-auto mt-8 pt-4 border-t border-[#064E3B]/10">
        <div className="flex items-center gap-2 text-xs text-[#4E6B5C] font-serif-heading italic">
          <Leaf className="w-3 h-3 text-[#064E3B]" />
          <span>Nature's wisdom. Responsible innovation.</span>
        </div>
      </div>
    </div>
  );
}
