import { fetchTTSAudioAPI } from './api';

let activeAudioElement: HTMLAudioElement | null = null;

const LANG_CODE_MAP: Record<string, string> = {
  en: 'en-IN',
  hi: 'hi-IN',
  te: 'te-IN',
  kn: 'kn-IN',
  'en-in': 'en-IN',
  'hi-in': 'hi-IN',
  'te-in': 'te-IN',
  'kn-in': 'kn-IN',
};

/**
 * Validate that text contains native script characters for the requested language.
 */
export function validateScriptForLanguage(text: string, lang: string): boolean {
  if (!text) return false;
  const cleanLang = (lang || 'en').toLowerCase().trim();
  if (cleanLang === 'kn' || cleanLang === 'kn-in') {
    return /[\u0c80-\u0cff]/.test(text);
  }
  if (cleanLang === 'te' || cleanLang === 'te-in') {
    return /[\u0c00-\u0c7f]/.test(text);
  }
  if (cleanLang === 'hi' || cleanLang === 'hi-in') {
    return /[\u0900-\u097f]/.test(text);
  }
  return true; // English requires no script validation
}

/**
 * Clean text for natural speech synthesis (remove markdown markers, URL icons, citations).
 */
export function cleanTextForTTS(rawText: string): string {
  if (!rawText) return '';
  return rawText
    .replace(/\[\d+\]/g, '') // remove citation brackets [1]
    .replace(/\[SOURCE_\d+\]/gi, '') // remove [SOURCE_1] labels
    .replace(/[#*`_~]/g, '') // remove markdown symbols
    .replace(/↗/g, '')
    .replace(/http[s]?:\/\/\S+/g, '') // remove URLs
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Stop any currently active speech synthesis or audio playback immediately.
 */
export function stopSpeaking(): void {
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    try {
      window.speechSynthesis.cancel();
    } catch (e) {
      console.warn('SpeechSynthesis cancel error:', e);
    }
  }

  if (activeAudioElement) {
    try {
      activeAudioElement.pause();
      activeAudioElement.currentTime = 0;
      activeAudioElement = null;
    } catch (e) {
      console.warn('Audio playback cancel error:', e);
    }
  }
}

/**
 * Check if browser is currently speaking or playing speech audio.
 */
export function isSpeaking(): boolean {
  if (activeAudioElement && !activeAudioElement.paused && !activeAudioElement.ended) {
    return true;
  }
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    return window.speechSynthesis.speaking;
  }
  return false;
}

/**
 * Retrieve best available voice for requested BCP-47 language code (en-IN, hi-IN, te-IN, kn-IN).
 */
export function getVoiceForLanguage(langCode: string): SpeechSynthesisVoice | null {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
    return null;
  }

  const targetLang = LANG_CODE_MAP[langCode.toLowerCase()] || langCode;
  const targetPrefix = targetLang.split('-')[0].toLowerCase();
  const voices = window.speechSynthesis.getVoices();

  if (!voices || voices.length === 0) return null;

  // 1. Exact BCP-47 match (e.g. te-IN)
  let best = voices.find(
    (v) => v.lang.toLowerCase().replace('_', '-') === targetLang.toLowerCase()
  );

  // 2. Exact prefix match (e.g. te)
  if (!best) {
    best = voices.find((v) => v.lang.toLowerCase().startsWith(targetPrefix));
  }

  // Return matching voice if prefix aligns, NEVER fall back to an English voice for non-English targets
  return best || null;
}

interface SpeakOptions {
  text: string;
  lang?: string;
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (err: any) => void;
}

/**
 * Speak text aloud using browser Web Speech API or backend TTS fallback.
 */
export async function speakText({ text, lang = 'en', onStart, onEnd, onError }: SpeakOptions): Promise<void> {
  const cleaned = cleanTextForTTS(text);
  if (!cleaned) {
    if (onEnd) onEnd();
    return;
  }

  const effectiveLang = (lang || 'en').toLowerCase().trim();
  const bcp47Lang = LANG_CODE_MAP[effectiveLang] || 'en-IN';

  // Script Alignment Check (Part 17)
  if (!validateScriptForLanguage(cleaned, effectiveLang)) {
    console.warn(
      `[SPEAK_TEXT_LANGUAGE_MISMATCH] answer_language=${effectiveLang} but text contains no matching script characters.`
    );
    if (onEnd) onEnd();
    return;
  }

  const matchingVoice = getVoiceForLanguage(effectiveLang);
  const availableVoices = typeof window !== 'undefined' && 'speechSynthesis' in window ? window.speechSynthesis.getVoices() : [];

  console.log('[SPEAK_RUNTIME]', {
    textLength: cleaned.length,
    language: effectiveLang,
    locale: bcp47Lang,
    voicesAvailable: availableVoices.length,
    selectedVoice: matchingVoice ? matchingVoice.name : 'NONE',
    selectedVoiceLang: matchingVoice ? matchingVoice.lang : 'NONE',
  });

  // Cancel any active speech before starting new speech
  stopSpeaking();

  // 1. If native browser voice matching the target language is available, use SpeechSynthesis
  if (matchingVoice && typeof window !== 'undefined' && 'speechSynthesis' in window) {
    const utterance = new SpeechSynthesisUtterance(cleaned);
    utterance.lang = bcp47Lang;
    utterance.voice = matchingVoice;
    utterance.rate = 0.95;

    utterance.onstart = () => {
      console.log('[SPEAK_START]');
      if (onStart) onStart();
    };

    utterance.onend = () => {
      console.log('[SPEAK_END]');
      if (onEnd) onEnd();
    };

    utterance.onerror = (evt) => {
      if (evt.error !== 'interrupted' && evt.error !== 'canceled') {
        console.error('[SPEAK_ERROR]', evt.error);
        if (onError) onError(evt);
      }
      if (onEnd) onEnd();
    };

    console.log('[SPEAK_STATE]', {
      speaking: window.speechSynthesis.speaking,
      pending: window.speechSynthesis.pending,
      paused: window.speechSynthesis.paused,
    });

    try {
      window.speechSynthesis.speak(utterance);
      return;
    } catch (err) {
      console.warn('SpeechSynthesis speak failed, falling back to backend TTS:', err);
    }
  }

  // 2. High-quality backend native TTS fallback (gTTS MP3 stream) with HTML5 Audio unlock
  try {
    // Unlock Audio element synchronously in user gesture
    const audio = new Audio();
    audio.src = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA';
    activeAudioElement = audio;

    // Play silent snippet to unlock audio on iOS/Chrome autoplay policies
    await audio.play().catch(() => {});

    if (onStart) onStart();

    console.log('[TTS_REQUEST]', {
      language: effectiveLang,
      text_length: cleaned.length,
    });

    const blob = await fetchTTSAudioAPI(cleaned, effectiveLang);

    console.log('[TTS_RESPONSE]', {
      status: 200,
      content_type: blob.type || 'audio/mpeg',
      bytes: blob.size,
    });

    if (blob.size === 0) {
      console.error('[TTS_ERROR] Backend returned 0 byte audio payload');
      activeAudioElement = null;
      if (onEnd) onEnd();
      return;
    }

    const audioUrl = URL.createObjectURL(blob);
    audio.src = audioUrl;

    audio.onended = () => {
      console.log('[TTS_PLAYBACK]', { ended: true });
      activeAudioElement = null;
      URL.revokeObjectURL(audioUrl);
      if (onEnd) onEnd();
    };

    audio.onerror = (evt) => {
      console.error('[AUDIO_PLAYBACK_ERROR]', evt);
      activeAudioElement = null;
      URL.revokeObjectURL(audioUrl);
      if (onError) onError(evt);
      if (onEnd) onEnd();
    };

    console.log('[TTS_PLAYBACK]', { started: true });
    await audio.play().catch((err) => {
      console.error('[AUDIO_PLAY_ERROR]', err);
      activeAudioElement = null;
      URL.revokeObjectURL(audioUrl);
      if (onError) onError(err);
      if (onEnd) onEnd();
    });
  } catch (err) {
    console.error('Backend TTS playback failed:', err);
    activeAudioElement = null;
    if (onError) onError(err);
    if (onEnd) onEnd();
  }
}


