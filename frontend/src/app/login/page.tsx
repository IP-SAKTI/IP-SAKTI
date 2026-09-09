'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Mail } from 'lucide-react';
import AuthLayout from '@/components/auth/AuthLayout';
import AuthInput from '@/components/auth/AuthInput';
import PasswordInput from '@/components/auth/PasswordInput';
import AuthButton from '@/components/auth/AuthButton';

import { useAuth } from '@/context/AuthContext';

export default function LoginPage() {
  const router = useRouter();
  const { user, isLoading: authLoading, login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [formError, setFormError] = useState('');

  // If user is already authenticated, redirect to /
  useEffect(() => {
    if (!authLoading && user) {
      router.push('/');
    }
  }, [user, authLoading, router]);

  // Explicitly reset form states on mount / unmount
  useEffect(() => {
    setEmail('');
    setPassword('');
    setEmailError('');
    setPasswordError('');
    setFormError('');
  }, []);

  const validate = () => {
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

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setIsLoading(true);
    setFormError('');

    try {
      const success = await login(email.trim(), password);
      if (success) {
        setEmail('');
        setPassword('');
        router.push('/');
      } else {
        setFormError('Invalid email or password credentials. Please try again.');
      }
    } catch (err) {
      setFormError('Authentication service failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout>
      {/* Login Title & Subtitle */}
      <div>
        <h2 className="font-serif-heading text-3xl font-bold text-white tracking-wide">
          Login
        </h2>
        <p className="text-xs text-[#82A997] mt-1 font-sans-body">
          Welcome back to IP-SAKTI
        </p>
      </div>

      {formError && (
        <div className="bg-red-900/40 border border-red-500/50 text-red-200 rounded-lg p-2.5 text-xs font-semibold">
          {formError}
        </div>
      )}

      <form onSubmit={handleLogin} noValidate className="space-y-4 font-sans-body">
        {/* Email Field */}
        <AuthInput
          label="Your Email"
          type="email"
          name="email"
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

        {/* Password Field */}
        <PasswordInput
          label="Your Password"
          name="password"
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

        {/* Remember Me & Forgot Password Row */}
        <div className="flex items-center justify-between pt-1 text-xs">
          <label className="flex items-center gap-2 cursor-pointer text-[#A1C9B6]">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="rounded bg-[#03241A] border-[#135A42] text-[#2B7A54] focus:ring-0 accent-[#2B7A54]"
            />
            <span>Remember me</span>
          </label>

          <a
            href="#"
            onClick={(e) => e.preventDefault()}
            className="text-[#2B7A54] hover:text-[#4FD68A] hover:underline font-medium transition-colors"
          >
            Forgot password?
          </a>
        </div>

        {/* Primary Button */}
        <AuthButton type="submit" isLoading={isLoading}>
          Login
        </AuthButton>
      </form>

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
