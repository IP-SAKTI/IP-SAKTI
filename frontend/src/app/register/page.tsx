'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { User, Mail } from 'lucide-react';
import AuthLayout from '@/components/auth/AuthLayout';
import AuthInput from '@/components/auth/AuthInput';
import PasswordInput from '@/components/auth/PasswordInput';
import AuthButton from '@/components/auth/AuthButton';

import { useAuth } from '@/context/AuthContext';

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [agreedTerms, setAgreedTerms] = useState(true);

  const [nameError, setNameError] = useState('');
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [confirmError, setConfirmError] = useState('');
  const [termsError, setTermsError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [formError, setFormError] = useState('');

  const validate = () => {
    let valid = true;
    setNameError('');
    setEmailError('');
    setPasswordError('');
    setConfirmError('');
    setTermsError('');
    setFormError('');

    if (!fullName.trim()) {
      setNameError('Please enter your full name.');
      valid = false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.trim()) {
      setEmailError('Please enter your email address.');
      valid = false;
    } else if (!emailRegex.test(email.trim())) {
      setEmailError('Please enter a valid email address.');
      valid = false;
    }

    if (!password) {
      setPasswordError('Please create a password.');
      valid = false;
    } else if (password.length < 6) {
      setPasswordError('Password must be at least 6 characters.');
      valid = false;
    }

    if (!confirmPassword) {
      setConfirmError('Please confirm your password.');
      valid = false;
    } else if (confirmPassword !== password) {
      setConfirmError('Passwords do not match.');
      valid = false;
    }

    if (!agreedTerms) {
      setTermsError('You must agree to the Terms of Service.');
      valid = false;
    }

    return valid;
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setIsLoading(true);
    setFormError('');

    try {
      const success = await register(fullName.trim(), email.trim(), password);
      if (success) {
        router.push('/');
      } else {
        setFormError('Failed to create account. Please try again.');
      }
    } catch (err) {
      setFormError('Registration service error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout>
      {/* Title & Subtitle */}
      <div>
        <h2 className="font-serif-heading text-3xl font-bold text-white tracking-wide">
          Register
        </h2>
        <p className="text-xs text-[#82A997] mt-1 font-sans-body">
          Join IP-SAKTI and be part of a knowledge-driven future.
        </p>
      </div>

      {formError && (
        <div className="bg-red-900/40 border border-red-500/50 text-red-200 rounded-lg p-2.5 text-xs font-semibold">
          {formError}
        </div>
      )}

      <form onSubmit={handleRegister} noValidate className="space-y-3.5 font-sans-body">
        {/* Full Name Field */}
        <AuthInput
          label="Full Name"
          type="text"
          required
          value={fullName}
          onChange={(e) => {
            setFullName(e.target.value);
            if (nameError) setNameError('');
          }}
          placeholder="Enter your full name"
          icon={User}
          error={nameError}
        />

        {/* Email Address Field */}
        <AuthInput
          label="Email Address"
          type="email"
          required
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            if (emailError) setEmailError('');
          }}
          placeholder="Enter your email address"
          icon={Mail}
          error={emailError}
        />

        {/* Create Password Field */}
        <PasswordInput
          label="Create Password"
          required
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            if (passwordError) setPasswordError('');
          }}
          placeholder="Create a password"
          error={passwordError}
        />

        {/* Confirm Password Field */}
        <PasswordInput
          label="Confirm Password"
          required
          value={confirmPassword}
          onChange={(e) => {
            setConfirmPassword(e.target.value);
            if (confirmError) setConfirmError('');
          }}
          placeholder="Confirm your password"
          error={confirmError}
        />

        {/* Terms Checkbox */}
        <div className="pt-1">
          <label className="flex items-start gap-2 cursor-pointer text-xs text-[#A1C9B6] leading-snug">
            <input
              type="checkbox"
              checked={agreedTerms}
              onChange={(e) => {
                setAgreedTerms(e.target.checked);
                if (termsError) setTermsError('');
              }}
              className="mt-0.5 rounded bg-[#03241A] border-[#135A42] text-[#2B7A54] focus:ring-0 accent-[#2B7A54]"
            />
            <span>
              I agree to the{' '}
              <a href="#" onClick={(e) => e.preventDefault()} className="text-[#2B7A54] underline hover:text-[#4FD68A]">
                Terms of Service
              </a>{' '}
              and{' '}
              <a href="#" onClick={(e) => e.preventDefault()} className="text-[#2B7A54] underline hover:text-[#4FD68A]">
                Privacy Policy
              </a>
              .
            </span>
          </label>
          {termsError && (
            <p className="text-[11px] text-red-400 font-medium pt-1">
              {termsError}
            </p>
          )}
        </div>

        {/* Primary Button */}
        <AuthButton type="submit" isLoading={isLoading}>
          Register
        </AuthButton>
      </form>

      {/* Navigation Link */}
      <div className="pt-4 border-t border-white/10 text-center text-xs text-[#82A997]">
        <span>Already a member? </span>
        <Link
          href="/login"
          className="text-[#2B7A54] hover:text-[#4FD68A] font-bold hover:underline ml-1 transition-colors"
        >
          Login here
        </Link>
      </div>
    </AuthLayout>
  );
}
