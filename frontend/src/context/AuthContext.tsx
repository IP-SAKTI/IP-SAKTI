'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

// ─────────────────────────────────────────────────────────────────────────────
// Cookie helpers — used by Next.js middleware for server-side route protection.
// The cookie is NOT an auth source-of-truth; it is only a routing hint.
// All real session validation is done via Supabase through /auth/verify.
// ─────────────────────────────────────────────────────────────────────────────

const SESSION_COOKIE_NAME = 'ipsakti_session';

/** Set the routing-hint cookie so middleware can gate protected routes. */
function setSessionCookie(): void {
  if (typeof document === 'undefined') return;
  // SameSite=Lax prevents CSRF; no Secure flag needed for localhost dev.
  document.cookie = `${SESSION_COOKIE_NAME}=1; path=/; SameSite=Lax`;
}

/** Clear the routing-hint cookie on logout or session expiry. */
function clearSessionCookie(): void {
  if (typeof document === 'undefined') return;
  document.cookie = `${SESSION_COOKIE_NAME}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax`;
}

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export interface UserProfile {
  fullName: string;
  email: string;
  organization: string;
  role: string;
  bio?: string;
  avatarUrl?: string;
}

export interface UserSession {
  id: string;
  email: string;
}

interface AuthContextType {
  user: UserSession | null;
  profile: UserProfile | null;
  /** True while the Supabase session check is in flight. */
  isLoading: boolean;
  login: (email: string, password?: string) => Promise<boolean>;
  register: (fullName: string, email: string, password?: string) => Promise<boolean>;
  updateProfile: (updated: Partial<UserProfile>) => Promise<boolean>;
  sendMagicLink: (email: string) => Promise<{ ok: boolean; message: string }>;
  logout: () => Promise<void>;
}

// ─────────────────────────────────────────────────────────────────────────────
// Context
// ─────────────────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextType>({
  user: null,
  profile: null,
  isLoading: true,
  login: async () => false,
  register: async () => false,
  updateProfile: async () => false,
  sendMagicLink: async () => ({ ok: false, message: 'Not initialized' }),
  logout: async () => {},
});

// ─────────────────────────────────────────────────────────────────────────────
// Provider
// ─────────────────────────────────────────────────────────────────────────────

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<UserSession | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  /**
   * isLoading starts TRUE and is set to FALSE only after the Supabase
   * session check completes (success or failure).
   * Protected pages must NOT render content until isLoading === false.
   */
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // ── Session verification on mount ─────────────────────────────────────────
  useEffect(() => {
    async function verifySession() {
      try {
        const token = localStorage.getItem('ipsakti_auth_token');

        if (!token) {
          // No stored token → definitively unauthenticated
          setUser(null);
          setProfile(null);
          clearSessionCookie();
          setIsLoading(false);
          return;
        }

        // Validate the stored token against Supabase via our backend proxy
        const res = await fetch(`${API_BASE}/auth/verify`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (res.ok) {
          const data = await res.json();
          if (data && data.user) {
            const verifiedUser: UserSession = {
              id: data.user.id,
              email: data.user.email || '',
            };
            const verifiedProfile: UserProfile = {
              fullName:
                data.user.name ||
                data.user.email?.split('@')[0] ||
                'Researcher',
              email: data.user.email || '',
              organization: 'IP-SAKTI',
              role: 'Researcher',
              bio: '',
              avatarUrl: '',
            };
            setUser(verifiedUser);
            setProfile(verifiedProfile);
            localStorage.setItem(
              'ipsakti_auth_session',
              JSON.stringify(verifiedUser)
            );
            localStorage.setItem(
              'ipsakti_user_profile',
              JSON.stringify(verifiedProfile)
            );
            // ← Cookie confirms a valid session exists for middleware
            setSessionCookie();
          } else {
            throw new Error('Invalid user payload from /auth/verify');
          }
        } else {
          // Token rejected by Supabase (expired or revoked)
          _clearAllAuthState();
        }
      } catch (err) {
        console.warn('Session verification failed:', err);
        _clearAllAuthState();
      } finally {
        setIsLoading(false);
      }
    }

    verifySession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [API_BASE]);

  // ── Internal helper — wipe all auth state ─────────────────────────────────
  function _clearAllAuthState(): void {
    setUser(null);
    setProfile(null);
    clearSessionCookie();
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('ipsakti_auth_token');
      localStorage.removeItem('ipsakti_auth_refresh_token');
      localStorage.removeItem('ipsakti_auth_session');
      localStorage.removeItem('ipsakti_user_profile');
      localStorage.removeItem('ipsakti_active_conversation_id');
    }
  }

  // ── Login with email + password ───────────────────────────────────────────
  const login = async (
    emailInput: string,
    passwordInput?: string
  ): Promise<boolean> => {
    setIsLoading(true);
    const cleanEmail = emailInput.trim().toLowerCase();
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: cleanEmail,
          password: passwordInput || '',
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const sessionData: UserSession = {
          id: data.user.id,
          email: data.user.email || cleanEmail,
        };
        const profileData: UserProfile = {
          fullName: data.user.name || cleanEmail.split('@')[0],
          email: data.user.email || cleanEmail,
          organization: 'IP-SAKTI',
          role: 'Researcher',
          bio: '',
          avatarUrl: '',
        };

        setUser(sessionData);
        setProfile(profileData);
        localStorage.setItem(
          'ipsakti_auth_session',
          JSON.stringify(sessionData)
        );
        localStorage.setItem(
          'ipsakti_user_profile',
          JSON.stringify(profileData)
        );
        if (data.token) {
          localStorage.setItem('ipsakti_auth_token', data.token);
        }
        // ← Set cookie so middleware recognises the session on next navigation
        setSessionCookie();
        setIsLoading(false);
        return true;
      }
    } catch (err) {
      console.warn('FastAPI auth login error:', err);
    }

    // Reject invalid credentials without any fallback
    _clearAllAuthState();
    setIsLoading(false);
    return false;
  };

  // ── Register ──────────────────────────────────────────────────────────────
  const register = async (
    fullNameInput: string,
    emailInput: string,
    passwordInput?: string
  ): Promise<boolean> => {
    setIsLoading(true);
    const cleanEmail = emailInput.trim().toLowerCase();
    const cleanName = fullNameInput.trim();
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: cleanName,
          email: cleanEmail,
          password: passwordInput || 'password',
          confirm_password: passwordInput || 'password',
          terms_accepted: true,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const sessionData: UserSession = {
          id: data.user.id,
          email: data.user.email || cleanEmail,
        };
        const profileData: UserProfile = {
          fullName: data.user.name || cleanName,
          email: data.user.email || cleanEmail,
          organization: 'IP-SAKTI',
          role: 'Researcher',
          bio: '',
          avatarUrl: '',
        };

        setUser(sessionData);
        setProfile(profileData);
        localStorage.setItem(
          'ipsakti_auth_session',
          JSON.stringify(sessionData)
        );
        localStorage.setItem(
          'ipsakti_user_profile',
          JSON.stringify(profileData)
        );
        if (data.token) {
          localStorage.setItem('ipsakti_auth_token', data.token);
        }
        setSessionCookie();
        setIsLoading(false);
        return true;
      }
    } catch (err) {
      console.warn('FastAPI auth register error:', err);
    }

    _clearAllAuthState();
    setIsLoading(false);
    return false;
  };

  // ── Update profile ────────────────────────────────────────────────────────
  const updateProfile = async (
    updated: Partial<UserProfile>
  ): Promise<boolean> => {
    return new Promise((resolve) => {
      setProfile((prev) => {
        const newProfile: UserProfile = {
          fullName: updated.fullName ?? prev?.fullName ?? 'User',
          email:
            updated.email ??
            prev?.email ??
            user?.email ??
            '',
          organization:
            updated.organization ?? prev?.organization ?? 'IP-SAKTI',
          role: updated.role ?? prev?.role ?? 'Researcher',
          bio:
            updated.bio !== undefined ? updated.bio : prev?.bio ?? '',
          avatarUrl:
            updated.avatarUrl !== undefined
              ? updated.avatarUrl
              : prev?.avatarUrl ?? '',
        };
        localStorage.setItem(
          'ipsakti_user_profile',
          JSON.stringify(newProfile)
        );
        return newProfile;
      });
      resolve(true);
    });
  };

  // ── Send Magic Link ───────────────────────────────────────────────────────
  /**
   * Triggers Supabase to send a passwordless sign-in email.
   * The link redirects the user to /auth/callback where the session is
   * established and the cookie is set before redirecting to the dashboard.
   */
  const sendMagicLink = async (
    email: string
  ): Promise<{ ok: boolean; message: string }> => {
    const cleanEmail = email.trim().toLowerCase();
    if (
      !cleanEmail ||
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(cleanEmail)
    ) {
      return { ok: false, message: 'Please enter a valid email address.' };
    }
    try {
      const res = await fetch(`${API_BASE}/auth/magic-link`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: cleanEmail,
          redirect_to: `${window.location.origin}/auth/callback`,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        return {
          ok: true,
          message:
            data.message || 'Magic link sent. Please check your email.',
        };
      }
      const errData = await res.json().catch(() => ({}));
      return {
        ok: false,
        message:
          errData.detail ||
          'Failed to send magic link. Please try again.',
      };
    } catch (err) {
      console.warn('sendMagicLink error:', err);
      return {
        ok: false,
        message:
          'Network error. Please check your connection and try again.',
      };
    }
  };

  // ── Logout ────────────────────────────────────────────────────────────────
  const logout = async (): Promise<void> => {
    const token =
      typeof window !== 'undefined'
        ? localStorage.getItem('ipsakti_auth_token')
        : null;

    // Clear state and cookie FIRST so middleware rejects on next navigation
    _clearAllAuthState();
    if (typeof sessionStorage !== 'undefined') {
      sessionStorage.clear();
    }

    // Then call Supabase logout (fire-and-forget — don't block redirect on it)
    if (token) {
      fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      }).catch((err) => console.warn('Logout API call failed:', err));
    }

    // Hard navigate so the middleware evaluates the cleared cookie immediately
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  };

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        isLoading,
        login,
        register,
        updateProfile,
        sendMagicLink,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
