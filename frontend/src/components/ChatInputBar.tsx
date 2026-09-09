'use client';

import React, { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { Search, Send, Loader2, Globe, Mic, Square, AlertCircle } from 'lucide-react';
import { transcribeAudio } from '@/lib/api';

interface ChatInputBarProps {
  onSendMessage: (query: string) => void;
  isLoading?: boolean;
}

export default function ChatInputBar({ onSendMessage, isLoading = false }: ChatInputBarProps) {
  const [query, setQuery] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioError, setAudioError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  const startRecording = async () => {
    setAudioError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];

      let mimeType = '';
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus';
      } else if (MediaRecorder.isTypeSupported('audio/webm')) {
        mimeType = 'audio/webm';
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mimeType = 'audio/mp4';
      }

      const mediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        if (timerRef.current) clearInterval(timerRef.current);
        setIsRecording(false);
        setRecordingTime(0);

        if (audioChunksRef.current.length === 0) {
          setAudioError('No audio recorded. Please try speaking again.');
          return;
        }

        const audioBlob = new Blob(audioChunksRef.current, {
          type: mediaRecorder.mimeType || 'audio/webm',
        });

        if (audioBlob.size < 100) {
          setAudioError('Audio recording was empty. Please speak clearly.');
          return;
        }

        setIsTranscribing(true);
        try {
          const res = await transcribeAudio(audioBlob);
          if (res.error && !res.transcript) {
            setAudioError(res.error);
          } else if (res.transcript) {
            setQuery((prev) => (prev ? `${prev.trim()} ${res.transcript.trim()}` : res.transcript.trim()));
            setTimeout(() => {
              inputRef.current?.focus();
            }, 100);
          }
        } catch (err: any) {
          console.error('Transcription error:', err);
          setAudioError(err.message || 'Failed to transcribe audio.');
        } finally {
          setIsTranscribing(false);
        }
      };

      mediaRecorder.start(250);
      setIsRecording(true);
      setRecordingTime(0);

      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (err: any) {
      console.error('Microphone access error:', err);
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setAudioError('Microphone permission denied. Please allow microphone access in browser settings.');
      } else {
        setAudioError('Could not access microphone: ' + (err.message || 'Unknown error'));
      }
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
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
    if (!trimmed || isLoading || isRecording || isTranscribing) return;
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

  return (
    <div className="w-full relative z-20 my-4 font-sans-body">
      <div className="flex flex-col bg-white border border-[#C8D7C2] rounded-xl p-2 shadow-sm hover:shadow-md focus-within:border-[#003E29] focus-within:ring-1 focus-within:ring-[#003E29]/20 transition-all">
        <div className="flex items-center gap-3 px-3 py-1">
          <Search className="w-4 h-4 text-[#385246] shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading || isRecording || isTranscribing}
            placeholder={
              isRecording
                ? `Listening... (${formatSeconds(recordingTime)}) - Click mic to stop`
                : isTranscribing
                ? 'Transcribing audio using Whisper model...'
                : 'Ask about Traditional Knowledge, patents, AYUSH or ABS... (English / हिन्दी)'
            }
            className="flex-1 bg-transparent py-2.5 text-sm text-[#003E29] placeholder-[#7C817A] focus:outline-none font-sans-body"
          />

          {/* Voice Input Mic Button */}
          <button
            type="button"
            onClick={toggleRecording}
            disabled={isLoading || isTranscribing}
            title={isRecording ? 'Stop recording' : 'Voice Input / Speak question'}
            aria-label={isRecording ? 'Stop voice recording' : 'Start voice input'}
            className={`h-10 px-2.5 rounded-lg flex items-center justify-center gap-1.5 transition-all duration-200 shrink-0 cursor-pointer ${
              isRecording
                ? 'bg-red-50 text-red-600 border border-red-200 animate-pulse font-medium text-xs'
                : isTranscribing
                ? 'bg-[#F0F4EF] text-[#003E29] border border-[#C8D7C2]/60 cursor-wait'
                : 'text-[#385246] hover:text-[#003E29] hover:bg-[#E8EFE5] border border-transparent'
            }`}
          >
            {isTranscribing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-[#003E29]" />
                <span className="text-[11px] font-medium hidden sm:inline text-[#003E29]">Transcribing</span>
              </>
            ) : isRecording ? (
              <>
                <Square className="w-3.5 h-3.5 fill-red-600 text-red-600" />
                <span className="text-[11px] font-semibold text-red-600">{formatSeconds(recordingTime)}</span>
              </>
            ) : (
              <Mic className="w-4 h-4" />
            )}
          </button>

          {/* Submit Search Button */}
          <button
            onClick={handleSubmit}
            disabled={!query.trim() || isLoading || isRecording || isTranscribing}
            aria-label="Submit research query"
            className="w-10 h-10 bg-[#003E29] hover:bg-[#044D34] disabled:bg-[#003E29]/30 text-white rounded-lg flex items-center justify-center transition-all duration-200 shrink-0 shadow-sm active:scale-95 cursor-pointer"
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
            <span>Multilingual query support · Voice input (Whisper STT) · Hindi/English</span>
          </div>
          <div className="hidden sm:block">Press Enter ↵ to submit</div>
        </div>
      </div>
    </div>
  );
}
