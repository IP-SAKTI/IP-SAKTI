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
        setUser(JSON.parse(savedSession));
      } else {
        // Initial session fallback for active state
        setUser(DEFAULT_SESSION);
        localStorage.setItem('ipsakti_auth_session', JSON.stringify(DEFAULT_SESSION));
      }

      if (savedProfile) {
        setProfile(JSON.parse(savedProfile));
      } else {
        setProfile(DEFAULT_PROFILE);
        localStorage.setItem('ipsakti_user_profile', JSON.stringify(DEFAULT_PROFILE));
      }
    } catch (err) {
      console.warn('Error reading authentication state from local storage:', err);
      setUser(DEFAULT_SESSION);
      setProfile(DEFAULT_PROFILE);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = async (emailInput: string): Promise<boolean> => {
    setIsLoading(true);
    return new Promise((resolve) => {
      setTimeout(() => {
        const sessionData: UserSession = {
          id: `usr-${Date.now()}`,
          email: emailInput,
        };

        let profileData: UserProfile = {
          fullName: emailInput.split('@')[0],
          email: emailInput,
          organization: 'IP-SAKTI',
          role: 'Researcher',
          bio: '',
          avatarUrl: '',
        };

        const existingProfile = localStorage.getItem('ipsakti_user_profile');
        if (existingProfile) {
          try {
            const parsed = JSON.parse(existingProfile);
            if (parsed.email === emailInput) {
              profileData = parsed;
            }
          } catch (e) {
            // fallback to profileData
          }
        }

        setUser(sessionData);
        setProfile(profileData);

        localStorage.setItem('ipsakti_auth_session', JSON.stringify(sessionData));
        localStorage.setItem('ipsakti_user_profile', JSON.stringify(profileData));

        setIsLoading(false);
        resolve(true);
      }, 500);
    });
  };

  const register = async (fullNameInput: string, emailInput: string): Promise<boolean> => {
    setIsLoading(true);
    return new Promise((resolve) => {
      setTimeout(() => {
        const sessionData: UserSession = {
          id: `usr-${Date.now()}`,
          email: emailInput,
        };

        const profileData: UserProfile = {
          fullName: fullNameInput,
          email: emailInput,
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
        resolve(true);
      }, 500);
    });
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
    localStorage.removeItem('ipsakti_auth_session');
    localStorage.removeItem('ipsakti_user_profile');
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
