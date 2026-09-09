'use client';

import React from 'react';

/**
 * BotanicalBackground - Minimal, non-intrusive botanical edge accents.
 * 70% Product UI / 20% Traditional Knowledge Identity / 10% Subtle Leaf Accents
 */
export default function BotanicalBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden opacity-30 select-none">
      {/* Top-Right Corner Accent */}
      <svg
        className="absolute -top-10 -right-10 w-72 h-72 text-[#003E29]"
        viewBox="0 0 200 200"
        fill="currentColor"
      >
        <path
          d="M180,20 Q120,60 140,120 Q160,180 190,190 Q170,130 190,70 Z"
          opacity="0.15"
        />
        <path
          d="M190,0 Q130,40 110,100 Q150,150 200,160 Q160,110 180,30 Z"
          opacity="0.25"
        />
      </svg>

      {/* Bottom-Left Corner Accent */}
      <svg
        className="absolute -bottom-10 -left-10 w-72 h-72 text-[#003E29]"
        viewBox="0 0 200 200"
        fill="currentColor"
      >
        <path
          d="M20,180 Q80,140 60,80 Q40,20 10,10 Q30,70 10,130 Z"
          opacity="0.15"
        />
        <path
          d="M0,190 Q70,150 90,90 Q50,40 0,30 Q40,90 20,160 Z"
          opacity="0.25"
        />
      </svg>
    </div>
  );
}
