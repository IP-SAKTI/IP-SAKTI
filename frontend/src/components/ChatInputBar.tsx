'use client';

import React, { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { Search, Send, Loader2, Globe, Mic, Square, AlertCircle, XCircle } from 'lucide-react';

interface ChatInputBarProps {
  onSendMessage: (query: string) => void;
  isLoading?: boolean;
}

const VOICE_LANGUAGES = [
  { code: 'en-IN', label: 'English (EN)' },
  { code: 'hi-IN', label: 'Hindi (हिन्दी)' },
  { code: 'te-IN', label: 'Telugu (తెలుగు)' },
  { code: 'kn-IN', label: 'Kannada (ಕನ್ನಡ)' },
];

export default function ChatInputBar({ onSendMessage, isLoading = false }: ChatInputBarProps) {
  const [query, setQuery] = useState('');
  const [selectedLang, setSelectedLang] = useState<string>('en-IN');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioError, setAudioError] = useState<string | null>(null);

  const recognitionRef = useRef<any>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const isCancelledRef = useRef<boolean>(false);
  const initialQueryRef = useRef<string>('');
  const hasReceivedSpeechRef = useRef<boolean>(false);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (e) {
          // Ignore cleanup errors
        }
      }
    };
  }, []);

  const startRecording = () => {
    setAudioError(null);
    isCancelledRef.current = false;
    hasReceivedSpeechRef.current = false;
    initialQueryRef.current = query;

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setAudioError('Voice input is not supported in this browser. Please use Google Chrome.');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;

      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = selectedLang;

      recognition.onstart = () => {
        console.log('VOICE START');
        setIsRecording(true);
        setRecordingTime(0);
        if (timerRef.current) clearInterval(timerRef.current);
        timerRef.current = setInterval(() => {
          setRecordingTime((prev) => prev + 1);
        }, 1000);
      };

      recognition.onresult = (event: any) => {
        if (isCancelledRef.current) return;

        const transcript = Array.from(event.results)
          .map((result: any) => result[0].transcript)
          .join('');

        console.log('VOICE RESULT:', transcript);

        if (transcript && transcript.trim()) {
          hasReceivedSpeechRef.current = true;
          const baseQuery = initialQueryRef.current.trim();
          const cleanTranscript = transcript.trim();
          setQuery(baseQuery ? `${baseQuery} ${cleanTranscript}` : cleanTranscript);
        }
      };

      recognition.onerror = (event: any) => {
        const errCode = event.error;
        const errMsg = event.message || '';
        console.log('VOICE ERROR:', errCode, errMsg);

        if (isCancelledRef.current || errCode === 'aborted') {
          // Do NOT show an error if intentionally cancelled or aborted
          return;
        }

        if (errCode === 'not-allowed' || errCode === 'permission-denied') {
          setAudioError('Microphone permission was denied.');
        } else if (errCode === 'audio-capture') {
          setAudioError('No microphone was detected.');
        } else if (errCode === 'no-speech') {
          if (!hasReceivedSpeechRef.current) {
            setAudioError('No speech detected. Please try speaking clearly.');
          }
        } else if (errCode === 'network') {
          setAudioError('Speech recognition network error. Please try again.');
        } else if (errCode !== 'service-not-allowed') {
          setAudioError(`Voice error: ${errCode || 'Unknown error'}`);
        }
      };

      recognition.onend = () => {
        console.log('VOICE END');
        if (timerRef.current) clearInterval(timerRef.current);
        setIsRecording(false);
        setRecordingTime(0);
        recognitionRef.current = null;

        if (isCancelledRef.current) {
          setQuery(initialQueryRef.current);
          setAudioError(null);
        } else {
          setTimeout(() => {
            inputRef.current?.focus();
          }, 100);
        }
      };

      recognition.start();
    } catch (err: any) {
      console.error('Speech recognition start error:', err);
      setAudioError('Could not start voice recognition: ' + (err.message || 'Unknown error'));
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {
        console.warn('Error stopping speech recognition:', e);
      }
    }
  };

  const cancelRecording = () => {
    isCancelledRef.current = true;
    if (timerRef.current) clearInterval(timerRef.current);
    setIsRecording(false);
    setRecordingTime(0);
    setAudioError(null);
    setQuery(initialQueryRef.current);

    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch (e) {
        console.warn('Error aborting speech recognition:', e);
      }
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleSubmit = () => {
    const trimmed = query.trim();
    if (!trimmed || isLoading || isRecording) return;
    onSendMessage(trimmed);
    setQuery('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const formatSeconds = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const activeLangObj = VOICE_LANGUAGES.find((l) => l.code === selectedLang) || VOICE_LANGUAGES[0];

  return (
    <div className="w-full relative z-20 my-4 font-sans-body">
      <div className="flex flex-col bg-white border border-[#C8D7C2] rounded-xl p-2 shadow-sm hover:shadow-md focus-within:border-[#003E29] focus-within:ring-1 focus-within:ring-[#003E29]/20 transition-all">
        <div className="flex items-center gap-2 sm:gap-3 px-3 py-1">
          <Search className="w-4 h-4 text-[#385246] shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading || isRecording}
            placeholder={
              isRecording
                ? `🔴 Listening (${activeLangObj.label})... (${formatSeconds(recordingTime)})`
                : 'Ask about Traditional Knowledge, patents, AYUSH or ABS... (English / हिन्दी / తెలుగు / ಕನ್ನಡ)'
            }
            className="flex-1 bg-transparent py-2.5 text-sm text-[#003E29] placeholder-[#7C817A] focus:outline-none font-sans-body"
          />

          {/* Voice Language Selector Dropdown */}
          <select
            value={selectedLang}
            onChange={(e) => setSelectedLang(e.target.value)}
            disabled={isRecording || isLoading}
            title="Select voice language"
            aria-label="Select voice language"
            className="h-9 text-xs font-medium text-[#003E29] bg-[#F0F5EE] border border-[#C8D7C2] hover:border-[#003E29] rounded-lg px-2 py-1 focus:outline-none cursor-pointer shrink-0 transition-colors"
          >
            {VOICE_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.label}
              </option>
            ))}
          </select>

          {/* Cancel Recording Button (Visible only during active recording) */}
          {isRecording && (
            <button
              type="button"
              onClick={cancelRecording}
              title="Cancel recording & discard voice input"
              aria-label="Cancel voice recording"
              className="h-9 px-2.5 rounded-lg flex items-center justify-center gap-1 bg-stone-100 text-stone-600 hover:text-red-600 hover:bg-red-50 border border-stone-200 text-xs font-medium transition-all shrink-0 cursor-pointer"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Cancel</span>
            </button>
          )}

          {/* Voice Input / Stop Recording Mic Button */}
          <button
            type="button"
            onClick={toggleRecording}
            disabled={isLoading}
            title={isRecording ? 'Stop speech recognition' : 'Start voice recognition'}
            aria-label={isRecording ? 'Stop voice recording' : 'Start voice input'}
            className={`h-9 px-2.5 rounded-lg flex items-center justify-center gap-1.5 transition-all duration-200 shrink-0 cursor-pointer ${
              isRecording
                ? 'bg-red-50 text-red-600 border border-red-200 animate-pulse font-medium text-xs'
                : 'text-[#385246] hover:text-[#003E29] hover:bg-[#E8EFE5] border border-transparent'
            }`}
          >
            {isRecording ? (
              <>
                <Square className="w-3.5 h-3.5 fill-red-600 text-red-600" />
                <span className="text-[11px] font-semibold text-red-600">Stop ({formatSeconds(recordingTime)})</span>
              </>
            ) : (
              <Mic className="w-4 h-4" />
            )}
          </button>

          {/* Submit Search Button */}
          <button
            onClick={handleSubmit}
            disabled={!query.trim() || isLoading || isRecording}
            aria-label="Submit research query"
            className="w-9 h-9 bg-[#003E29] hover:bg-[#044D34] disabled:bg-[#003E29]/30 text-white rounded-lg flex items-center justify-center transition-all duration-200 shrink-0 shadow-sm active:scale-95 cursor-pointer"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin text-white" />
            ) : (
              <Send className="w-4 h-4 text-white ml-0.5" />
            )}
          </button>
        </div>

        {/* Audio Error Alert Banner */}
        {audioError && (
          <div className="mx-3 my-1 px-3 py-1.5 bg-amber-50 border border-amber-200 text-amber-800 rounded-md text-xs flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
              <span>{audioError}</span>
            </div>
            <button
              onClick={() => setAudioError(null)}
              className="text-amber-600 hover:text-amber-900 font-bold ml-2 cursor-pointer"
            >
              ×
            </button>
          </div>
        )}

        {/* Bottom Helper Bar */}
        <div className="flex items-center justify-between px-3 pt-1 pb-1 border-t border-[#C8D7C2]/40 text-[11px] text-[#7B9F8E]">
          <div className="flex items-center gap-1.5">
            <Globe className="w-3 h-3 text-[#385246]" />
            <span>Browser Web Speech API · Voice input (English / Hindi / Telugu / Kannada)</span>
          </div>
          <div className="hidden sm:block">Press Enter ↵ to submit</div>
        </div>
      </div>
    </div>
  );
}
