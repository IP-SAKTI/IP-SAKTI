'use client';

import React from 'react';

interface IpSaktiLogoProps {
  className?: string;
  variant?: 'light' | 'dark';
  alt?: string;
}

export default function IpSaktiLogo({
  className = 'h-10 w-auto object-contain',
  variant = 'light',
  alt = 'IP-SAKTI SAHAYAK',
}: IpSaktiLogoProps) {
  const filterStyle =
    variant === 'dark'
      ? 'brightness-0 invert opacity-95 hover:opacity-100 transition-opacity'
      : '';

  return (
    <img
      src="/assests/ip-sakthi/logo/ip-sakti-logo.png"
      alt={alt}
      className={`object-contain select-none ${filterStyle} ${className}`}
    />
  );
}
