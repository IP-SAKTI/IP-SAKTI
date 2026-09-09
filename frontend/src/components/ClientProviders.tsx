'use client';

import React from 'react';
import { AuthProvider } from '@/context/AuthContext';

export default function ClientProviders({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}
