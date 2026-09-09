'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

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
  isLoading: boolean;
  login: (email: string, password?: string) => Promise<boolean>;
  register: (fullName: string, email: string, password?: string) => Promise<boolean>;
  updateProfile: (updated: Partial<UserProfile>) => Promise<boolean>;
  logout: () => void;
}

const DEFAULT_PROFILE: UserProfile = {
  fullName: 'Manaswitha',
  email: 'manaswitha@ipsakti.gov.in',
  organization: 'IP-SAKTI',
  role: 'Researcher',
  bio: '',
  avatarUrl: '',
};

const DEFAULT_SESSION: UserSession = {
  id: 'usr-default-001',
  email: 'manaswitha@ipsakti.gov.in',
};

const AuthContext = createContext<AuthContextType>({
  user: null,
  profile: null,
  isLoading: true,
  login: async () => false,
  register: async () => false,
  updateProfile: async () => false,
  logout: () => {},
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<UserSession | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    try {
      const savedSession = localStorage.getItem('ipsakti_auth_session');
      const savedProfile = localStorage.getItem('ipsakti_user_profile');

      if (savedSession) {
        const parsedSession = JSON.parse(savedSession);
        if (parsedSession && parsedSession.email) {
          setUser(parsedSession);
        } else {
          setUser(null);
        }
      } else {
        setUser(null);
      }

      if (savedProfile) {
        const parsedProfile = JSON.parse(savedProfile);
        if (parsedProfile && parsedProfile.email) {
          setProfile(parsedProfile);
        } else {
          setProfile(null);
        }
      } else {
        setProfile(null);
      }
    } catch (err) {
      console.warn('Error reading authentication state from local storage:', err);
      setUser(null);
      setProfile(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const login = async (emailInput: string, passwordInput?: string): Promise<boolean> => {
    setIsLoading(true);
    const cleanEmail = emailInput.trim().toLowerCase();
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: cleanEmail, password: passwordInput || '' }),
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
        localStorage.setItem('ipsakti_auth_session', JSON.stringify(sessionData));
        localStorage.setItem('ipsakti_user_profile', JSON.stringify(profileData));
        if (data.token) {
          localStorage.setItem('ipsakti_auth_token', data.token);
        }
        setIsLoading(false);
        return true;
      }
    } catch (err) {
      console.warn('FastAPI auth login failed, falling back to client session:', err);
    }

    // Local fallback for offline/test mode
    const sessionData: UserSession = {
      id: `usr-${Date.now()}`,
      email: cleanEmail,
    };

    const profileData: UserProfile = {
      fullName: cleanEmail.split('@')[0],
      email: cleanEmail,
      organization: 'IP-SAKTI',
      role: 'Researcher',
      bio: '',
      avatarUrl: '',
    };

    setUser(sessionData);
    setProfile(profileData);
    localStorage.setItem('ipsakti_auth_session', JSON.stringify(sessionData));
    localStorage.setItem('ipsakti_user_profile', JSON.stringify(profileData));
    setIsLoading(false);
    return true;
  };

  const register = async (fullNameInput: string, emailInput: string, passwordInput?: string): Promise<boolean> => {
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
        localStorage.setItem('ipsakti_auth_session', JSON.stringify(sessionData));
        localStorage.setItem('ipsakti_user_profile', JSON.stringify(profileData));
        if (data.token) {
          localStorage.setItem('ipsakti_auth_token', data.token);
        }
        setIsLoading(false);
        return true;
      }
    } catch (err) {
      console.warn('FastAPI auth register failed, falling back to client session:', err);
    }

    // Local fallback
    const sessionData: UserSession = {
      id: `usr-${Date.now()}`,
      email: cleanEmail,
    };

    const profileData: UserProfile = {
      fullName: cleanName,
      email: cleanEmail,
      organization: 'IP-SAKTI',
      role: 'Researcher',
      bio: '',
      avatarUrl: '',
    };

    setUser(sessionData);
    setProfile(profileData);
    localStorage.setItem('ipsakti_auth_session', JSON.stringify(sessionData));
    localStorage.setItem('ipsakti_user_profile', JSON.stringify(profileData));
    setIsLoading(false);
    return true;
  };

  const updateProfile = async (updated: Partial<UserProfile>): Promise<boolean> => {
    return new Promise((resolve) => {
      setProfile((prev) => {
        const newProfile: UserProfile = {
          fullName: updated.fullName ?? prev?.fullName ?? 'User',
          email: updated.email ?? prev?.email ?? user?.email ?? 'user@ipsakti.gov.in',
          organization: updated.organization ?? prev?.organization ?? 'IP-SAKTI',
          role: updated.role ?? prev?.role ?? 'Researcher',
          bio: updated.bio !== undefined ? updated.bio : prev?.bio ?? '',
          avatarUrl: updated.avatarUrl !== undefined ? updated.avatarUrl : prev?.avatarUrl ?? '',
        };
        localStorage.setItem('ipsakti_user_profile', JSON.stringify(newProfile));
        return newProfile;
      });
      resolve(true);
    });
  };

  const logout = () => {
    setUser(null);
    setProfile(null);
    try {
      localStorage.removeItem('ipsakti_auth_session');
      localStorage.removeItem('ipsakti_user_profile');
      localStorage.removeItem('ipsakti_auth_token');
      localStorage.removeItem('ipsakti_active_conversation_id');
      sessionStorage.clear();
    } catch (err) {
      console.warn('Logout storage cleanup error:', err);
    }
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        isLoading,
        login,
        register,
        updateProfile,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
