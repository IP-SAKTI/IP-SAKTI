'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Mail, Zap, Lock } from 'lucide-react';
import AuthLayout from '@/components/auth/AuthLayout';
import AuthInput from '@/components/auth/AuthInput';
import PasswordInput from '@/components/auth/PasswordInput';
import AuthButton from '@/components/auth/AuthButton';

import { useAuth } from '@/context/AuthContext';

type AuthMode = 'password' | 'magic';

export default function LoginPage() {
  const router = useRouter();
  const { user, isLoading: authLoading, login, sendMagicLink } = useAuth();

  // Shared
  const [mode, setMode] = useState<AuthMode>('magic');
  const [email, setEmail] = useState('');

  // Password mode
  const [password, setPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');

  // Shared error / status
  const [emailError, setEmailError] = useState('');
  const [formError, setFormError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Magic link sent confirmation
  const [magicLinkSent, setMagicLinkSent] = useState(false);
  const [magicLinkEmail, setMagicLinkEmail] = useState('');

  // If user is already authenticated, redirect to dashboard
  useEffect(() => {
    if (!authLoading && user) {
      router.push('/');
    }
  }, [user, authLoading, router]);

  // Reset form fields on mount
  useEffect(() => {
    setEmail('');
    setPassword('');
    setEmailError('');
    setPasswordError('');
    setFormError('');
    setMagicLinkSent(false);
  }, []);

  // Reset error messages when switching modes
  const switchMode = (newMode: AuthMode) => {
    setMode(newMode);
    setEmailError('');
    setPasswordError('');
    setFormError('');
    setMagicLinkSent(false);
    setPassword('');
  };

  // ── Password Login ──────────────────────────────────────────────
  const validatePassword = () => {
    let valid = true;
    setEmailError('');
    setPasswordError('');
    setFormError('');

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.trim()) {
      setEmailError('Please enter your email address.');
      valid = false;
    } else if (!emailRegex.test(email.trim())) {
      setEmailError('Please enter a valid email address.');
      valid = false;
    }
    if (!password) {
      setPasswordError('Please enter your password.');
      valid = false;
    }
    return valid;
  };

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validatePassword()) return;
    setIsLoading(true);
    setFormError('');
    try {
      const success = await login(email.trim(), password);
      if (success) {
        setEmail('');
        setPassword('');
        router.push('/');
      } else {
        setFormError('Invalid email or password. Please try again.');
      }
    } catch {
      setFormError('Authentication service failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // ── Magic Link ──────────────────────────────────────────────────
  const validateEmail = () => {
    setEmailError('');
    setFormError('');
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.trim()) {
      setEmailError('Please enter your email address.');
      return false;
    }
    if (!emailRegex.test(email.trim())) {
      setEmailError('Please enter a valid email address.');
      return false;
    }
    return true;
  };

  const handleMagicLink = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateEmail()) return;
    setIsLoading(true);
    setFormError('');
    try {
      const result = await sendMagicLink(email.trim());
      if (result.ok) {
        setMagicLinkSent(true);
        setMagicLinkEmail(email.trim());
        setEmail('');
      } else {
        setFormError(result.message);
      }
    } catch {
      setFormError('Failed to send magic link. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // ── Render ──────────────────────────────────────────────────────
  return (
    <AuthLayout>
      {/* Title */}
      <div>
        <h2 className="font-serif-heading text-3xl font-bold text-white tracking-wide">
          Login
        </h2>
        <p className="text-xs text-[#82A997] mt-1 font-sans-body">
          Welcome back to IP-SAKTI
        </p>
      </div>

      {/* Mode Toggle Tabs */}
      <div className="flex rounded-xl overflow-hidden border border-[#14533C]/60 bg-[#02281A]">
        <button
          type="button"
          id="tab-magic-link"
          onClick={() => switchMode('magic')}
          className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-semibold transition-colors cursor-pointer ${
            mode === 'magic'
              ? 'bg-[#2B7A54] text-white'
              : 'text-[#82A997] hover:text-white hover:bg-[#14533C]/40'
          }`}
        >
          <Zap className="w-3.5 h-3.5" />
          Magic Link
        </button>
        <button
          type="button"
          id="tab-password"
          onClick={() => switchMode('password')}
          className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-semibold transition-colors cursor-pointer ${
            mode === 'password'
              ? 'bg-[#2B7A54] text-white'
              : 'text-[#82A997] hover:text-white hover:bg-[#14533C]/40'
          }`}
        >
          <Lock className="w-3.5 h-3.5" />
          Password
        </button>
      </div>

      {/* ── Magic Link Form ── */}
      {mode === 'magic' && (
        <>
          {magicLinkSent ? (
            /* Success state */
            <div className="space-y-4">
              <div className="bg-emerald-900/40 border border-emerald-500/50 rounded-xl p-4 text-center space-y-2">
                <div className="flex items-center justify-center">
                  <span className="text-2xl">✉️</span>
                </div>
                <p className="text-emerald-200 font-semibold text-sm">
                  Magic link sent!
                </p>
                <p className="text-emerald-300/80 text-xs leading-relaxed">
                  We sent a sign-in link to{' '}
                  <span className="font-bold text-emerald-200">{magicLinkEmail}</span>.
                  Click the link in your email to sign in — no password needed.
                </p>
                <p className="text-[#82A997] text-[11px]">
                  Check your spam folder if you don't see it within a minute.
                </p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setMagicLinkSent(false);
                  setMagicLinkEmail('');
                  setEmail('');
                }}
                className="w-full text-center text-xs text-[#2B7A54] hover:text-[#4FD68A] font-semibold transition-colors cursor-pointer"
              >
                Send to a different email
              </button>
            </div>
          ) : (
            /* Magic link email input form */
            <form onSubmit={handleMagicLink} noValidate className="space-y-4 font-sans-body">
              <div className="text-xs text-[#82A997] leading-relaxed bg-[#02281A]/60 border border-[#14533C]/40 rounded-lg p-3">
                Enter your email and we'll send you a secure sign-in link.{' '}
                <span className="text-emerald-400 font-semibold">No password required.</span>
              </div>

              {formError && (
                <div className="bg-red-900/40 border border-red-500/50 text-red-200 rounded-lg p-2.5 text-xs font-semibold">
                  {formError}
                </div>
              )}

              <AuthInput
                label="Your Email"
                type="email"
                name="email"
                id="magic-email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (emailError) setEmailError('');
                }}
                placeholder="Enter your email"
                icon={Mail}
                error={emailError}
              />

              <AuthButton type="submit" isLoading={isLoading}>
                Send Magic Link
              </AuthButton>
            </form>
          )}
        </>
      )}

      {/* ── Password Form ── */}
      {mode === 'password' && (
        <form onSubmit={handlePasswordLogin} noValidate className="space-y-4 font-sans-body">
          {formError && (
            <div className="bg-red-900/40 border border-red-500/50 text-red-200 rounded-lg p-2.5 text-xs font-semibold">
              {formError}
            </div>
          )}

          <AuthInput
            label="Your Email"
            type="email"
            name="email"
            id="password-email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (emailError) setEmailError('');
            }}
            placeholder="Enter your email"
            icon={Mail}
            error={emailError}
          />

          <PasswordInput
            label="Your Password"
            name="password"
            id="password-field"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              if (passwordError) setPasswordError('');
            }}
            placeholder="Enter your password"
            error={passwordError}
          />

          <div className="flex items-center justify-end pt-1 text-xs">
            <a
              href="#"
              onClick={(e) => e.preventDefault()}
              className="text-[#2B7A54] hover:text-[#4FD68A] hover:underline font-medium transition-colors"
            >
              Forgot password?
            </a>
          </div>

          <AuthButton type="submit" isLoading={isLoading}>
            Login
          </AuthButton>
        </form>
      )}

      {/* Navigation Link */}
      <div className="pt-4 border-t border-white/10 text-center text-xs text-[#82A997]">
        <span>Don't have an account? </span>
        <Link
          href="/register"
          className="text-[#2B7A54] hover:text-[#4FD68A] font-bold hover:underline ml-1 transition-colors"
        >
          Register here
        </Link>
      </div>
    </AuthLayout>
  );
}
