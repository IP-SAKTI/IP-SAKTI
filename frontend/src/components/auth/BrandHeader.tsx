'use client';

import React from 'react';
import IpSaktiLogo from '../IpSaktiLogo';

export default function BrandHeader() {
  return (
    <div className="w-full flex flex-wrap items-center justify-between gap-4 font-sans-body pb-3 border-b border-[#064E3B]/10">
      {/* Top Left: Single Complete New IP-SAKTI Branding Element */}
      <div className="flex items-center">
        <IpSaktiLogo className="h-10 md:h-11 w-auto max-w-[220px] md:max-w-[250px] object-contain" />
      </div>

      {/* Top Right: Institutional Government Label */}
      <div className="text-right">
        <div className="text-[9px] font-bold tracking-widest text-[#064E3B] uppercase">
          GOVERNMENT OF INDIA INITIATIVES
        </div>
        <div className="text-[8.5px] font-medium tracking-wider text-[#385246] uppercase mt-0.5">
          PEOPLE &nbsp;|&nbsp; KNOWLEDGE &nbsp;|&nbsp; NATURE &nbsp;|&nbsp; BHARAT
        </div>
      </div>
    </div>
  );
}
