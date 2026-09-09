'use client';

/**
 * /auth/callback — Magic Link Session Establishment Page
 *
 * Supabase redirects the user here after they click a Magic Link email.
 * The URL contains session tokens in the hash fragment, e.g.:
 *   http://localhost:3000/auth/callback#access_token=xxx&refresh_token=yyy&type=magiclink
 *
 * This page:
 *  1. Reads the hash fragment from window.location.hash
 *  2. Stores the access_token in localStorage (ipsakti_auth_token)
 *  3. Calls GET /auth/verify to validate the token with Supabase and hydrate the AuthContext
 *  4. Redirects to the research dashboard on success, or /login on failure
 */

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2, CheckCircle2, AlertTriangle } from 'lucide-react';

type CallbackState = 'verifying' | 'success' | 'error';

export default function AuthCallbackPage() {
  const router = useRouter();
  const [state, setState] = useState<CallbackState>('verifying');
  const [message, setMessage] = useState('Verifying your magic link…');

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    async function handleCallback() {
      try {
        // --- 1. Parse hash fragment -----------------------------------------------
        const hash = window.location.hash;
        if (!hash || !hash.includes('access_token')) {
          setMessage('No session token found in the link. The link may be expired or invalid.');
          setState('error');
          setTimeout(() => router.push('/login'), 3000);
          return;
        }

        // Parse "key=value" pairs from the fragment (strip leading #)
        const params = new URLSearchParams(hash.substring(1));
        const accessToken = params.get('access_token');
        const linkType = params.get('type'); // 'magiclink' | 'recovery' | etc.

        if (!accessToken) {
          setMessage('Missing access token in magic link. Please request a new link.');
          setState('error');
          setTimeout(() => router.push('/login'), 3000);
          return;
        }

        // --- 2. Store token in localStorage ----------------------------------------
        localStorage.setItem('ipsakti_auth_token', accessToken);

        const refreshToken = params.get('refresh_token');
        if (refreshToken) {
          localStorage.setItem('ipsakti_auth_refresh_token', refreshToken);
        }

        // --- 3. Verify token with backend (Supabase GoTrue validation) ---------------
        const res = await fetch(`${API_BASE}/auth/verify`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        });

        if (!res.ok) {
          localStorage.removeItem('ipsakti_auth_token');
          localStorage.removeItem('ipsakti_auth_refresh_token');
          setMessage('Magic link has expired or was already used. Please request a new one.');
          setState('error');
          setTimeout(() => router.push('/login'), 3000);
          return;
        }

        const data = await res.json();

        // --- 4. Hydrate session in localStorage so AuthContext picks it up ----------
        if (data && data.user) {
          const sessionData = { id: data.user.id, email: data.user.email };
          const profileData = {
            fullName: data.user.name || data.user.email?.split('@')[0] || 'Researcher',
            email: data.user.email || '',
            organization: 'IP-SAKTI',
            role: 'Researcher',
            bio: '',
            avatarUrl: '',
          };
          localStorage.setItem('ipsakti_auth_session', JSON.stringify(sessionData));
          localStorage.setItem('ipsakti_user_profile', JSON.stringify(profileData));
        }

        // Clean hash from URL before redirecting (security hygiene)
        if (window.history.replaceState) {
          window.history.replaceState(null, '', window.location.pathname);
        }

        setMessage(`Welcome! Signing you in${data?.user?.email ? ` as ${data.user.email}` : ''}…`);
        setState('success');

        // --- 5. Redirect to dashboard -----------------------------------------------
        setTimeout(() => router.push('/'), 1200);
      } catch (err) {
        console.error('Auth callback error:', err);
        setMessage('An unexpected error occurred. Redirecting to login…');
        setState('error');
        setTimeout(() => router.push('/login'), 3000);
      }
    }

    handleCallback();
  }, [API_BASE, router]);

  return (
    <div className="min-h-screen w-full bg-[#02281A] flex items-center justify-center p-6">
      <div className="w-full max-w-sm bg-[#032619]/95 border border-[#14533C]/60 rounded-2xl p-8 shadow-2xl text-center space-y-5">
        {/* Logo mark */}
        <div className="flex items-center justify-center gap-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-emerald-600/30 border border-emerald-500/40 flex items-center justify-center">
            <span className="text-emerald-400 text-sm font-bold">IP</span>
          </div>
          <span className="text-white font-bold text-sm tracking-wide">IP-SAKTI Sahayak</span>
        </div>

        {/* Status icon */}
        <div className="flex items-center justify-center">
          {state === 'verifying' && (
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
          )}
          {state === 'success' && (
            <CheckCircle2 className="w-10 h-10 text-emerald-400" />
          )}
          {state === 'error' && (
            <AlertTriangle className="w-10 h-10 text-amber-400" />
          )}
        </div>

        {/* Status text */}
        <div>
          <h2 className="text-white font-semibold text-base leading-snug">
            {state === 'verifying' && 'Verifying Magic Link'}
            {state === 'success' && 'Sign-In Successful'}
            {state === 'error' && 'Sign-In Failed'}
          </h2>
          <p className="text-[#82A997] text-xs mt-1.5 leading-relaxed">
            {message}
          </p>
        </div>

        {/* Progress bar for verifying/success */}
        {(state === 'verifying' || state === 'success') && (
          <div className="w-full bg-[#14533C]/40 rounded-full h-1 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-1000 ${
                state === 'success' ? 'w-full bg-emerald-400' : 'w-1/3 bg-emerald-600 animate-pulse'
              }`}
            />
          </div>
        )}

        {state === 'error' && (
          <button
            onClick={() => router.push('/login')}
            className="w-full h-10 bg-[#2B7A54] hover:bg-[#236746] text-white text-sm font-semibold rounded-xl transition-colors"
          >
            Back to Login
          </button>
        )}
      </div>
    </div>
  );
}
