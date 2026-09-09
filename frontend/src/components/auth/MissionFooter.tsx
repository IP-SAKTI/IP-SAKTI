'use client';

import React from 'react';

export default function MissionFooter() {
  return (
    <div className="w-full space-y-4 pt-6 font-sans-body border-t border-[#064E3B]/10 relative">
      {/* Accent Green Bar + Mission Text */}
      <div className="space-y-1">
        <div className="w-6 h-0.5 bg-[#064E3B]" />
        <p className="font-serif-heading italic text-xs md:text-sm text-[#064E3B] leading-relaxed font-semibold">
          Preserving heritage. Enabling innovation. <br />
          For a stronger, healthier Bharat.
        </p>
      </div>

      {/* Low-Contrast Indian Heritage Architecture Silhouette Line-Art */}
      <div className="w-full h-12 overflow-hidden opacity-25 pointer-events-none flex items-end justify-center select-none pt-2">
        <svg
          className="w-full h-full text-[#064E3B]"
          viewBox="0 0 1000 120"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          {/* Qutub Minar Silhouette */}
          <path d="M80,120 L85,40 L95,40 L100,120 M83,60 L97,60 M82,80 L98,80 M81,100 L99,100" />

          {/* India Gate Silhouette */}
          <path d="M220,120 L220,50 L280,50 L280,120 M235,120 A20,20 0 0,1 265,120 M210,50 L290,50 M215,40 L285,40" />

          {/* Sanchi Stupa Dome */}
          <path d="M400,120 A50,50 0 0,1 500,120 M445,70 L455,40 L455,70 M440,40 L460,40" />

          {/* Taj Mahal / Parliament Dome */}
          <path d="M620,120 L620,70 Q650,40 680,70 L680,120 M635,120 A15,15 0 0,1 665,120 M640,40 L660,40 M650,40 L650,20" />

          {/* Red Fort / Monument Pillars */}
          <path d="M820,120 L820,60 L840,60 L840,120 M830,60 L830,40 M860,120 L860,60 L880,60 L880,120 M870,60 L870,40 M810,60 L890,60" />

          {/* Connecting Base Groundline */}
          <line x1="0" y1="120" x2="1000" y2="120" />
        </svg>
      </div>
    </div>
  );
}
