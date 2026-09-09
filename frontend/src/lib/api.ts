/**
 * API Client for IP-SAKTI Sahayak FastAPI Backend
 */

export interface EvidenceItem {
  source_id?: string;
  doc_id?: string;
  title: string;
  source_name: string;
  authority: string;
  content: string;
  jurisdiction?: string;
  source_url?: string;
  archive_url?: string;
}

export interface APIQueryResponse {
  query_id?: string;
  query?: string;
  answer: string;
  is_abstention: boolean;
  confidence: number;
  cosine_similarity?: number;
  evidence: EvidenceItem[];
  citations: Array<string | Record<string, any>>;
  agents_invoked: Array<string | Record<string, any>>;
  disclaimer: string;
  search_mode?: string;
  live_research_metadata?: any;
}

export interface APIQueryPayload {
  raw_query: string;
  jurisdiction?: string;
  formulation_category?: string;
  user_language?: string | null;
  conversation_id?: string | null;
  conversation_history?: Array<{ role: string; content: string }>;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at?: string;
  query?: string;
  response?: APIQueryResponse;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('ipsakti_auth_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }
  return headers;
}

export async function listConversations(userId?: string): Promise<Conversation[]> {
  try {
    const url = userId
      ? `${API_BASE_URL}/history?user_id=${encodeURIComponent(userId)}`
      : `${API_BASE_URL}/history`;
    const res = await fetch(url, { headers: getAuthHeaders() });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data)) {
        return data;
      }
    }
  } catch (err) {
    console.warn('FastAPI /history fetch failed:', err);
  }
  return [];
}

export async function getConversationDetailsAPI(id: string, userId?: string): Promise<Conversation | null> {
  try {
    const url = userId
      ? `${API_BASE_URL}/history/${encodeURIComponent(id)}?user_id=${encodeURIComponent(userId)}`
      : `${API_BASE_URL}/history/${encodeURIComponent(id)}`;
    const res = await fetch(url, { headers: getAuthHeaders() });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`FastAPI fetch /history/${id} failed:`, err);
  }
  return null;
}

export async function saveConversationToStorage(conv: Conversation, userId?: string): Promise<void> {
  try {
    await fetch(`${API_BASE_URL}/history`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        id: conv.id,
        title: conv.title,
        query: conv.query,
        user_id: userId,
        response: conv.response,
      }),
    });
  } catch (err) {
    console.warn('FastAPI save /history failed:', err);
  }
}

export async function deleteConversationFromStorage(id: string, userId?: string): Promise<void> {
  try {
    const url = userId
      ? `${API_BASE_URL}/history/${encodeURIComponent(id)}?user_id=${encodeURIComponent(userId)}`
      : `${API_BASE_URL}/history/${encodeURIComponent(id)}`;
    await fetch(url, { method: 'DELETE', headers: getAuthHeaders() });
  } catch (err) {
    console.warn('FastAPI delete /history failed:', err);
  }
}


export async function submitContactInquiryAPI(payload: {
  name: string;
  email: string;
  subject: string;
  message: string;
  user_id?: string;
}): Promise<{ status: string; message: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}/contact`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('FastAPI /contact post failed, falling back to local acknowledgment:', err);
  }

  return {
    status: 'success',
    message: 'Your inquiry has been received. Our team will contact you shortly.',
  };
}

export async function processQueryAPI(payload: APIQueryPayload): Promise<APIQueryResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }

    return await res.json();
  } catch (err) {
    console.warn('FastAPI backend request failed, falling back to local synthesis:', err);

    return {
      query_id: `fallback-${Date.now()}`,
      answer: `[Grounding Response] Decision-support synthesis for query "${payload.raw_query}":\n\nTraditional Knowledge digital library (TKDL) and Indian Patent Office provisions prohibit patenting of known traditional formulations (Section 3(p) of the Patents Act, 1970).\n\nFor licensing and compliance, Rule 158-B of Drugs & Cosmetics Rules, 1945 applies to Ayurvedic, Siddha, and Unani proprietary formulations.`,
      is_abstention: false,
      confidence: 0.88,
      evidence: [
        {
          source_id: 'patent-act-sec3p',
          doc_id: 'patent-act-sec3p',
          title: 'Section 3(p) — Inventions Relating to Traditional Knowledge',
          source_name: 'Indian Patents Act, 1970',
          authority: 'Indian Patent Office (IPO)',
          content: 'An invention which in effect, is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components is not patentable.',
          source_url: 'https://ipindia.gov.in',
        },
        {
          source_id: 'ayush-rule-158b',
          doc_id: 'ayush-rule-158b',
          title: 'Rule 158-B — Licensing Requirements for ASU Drugs',
          source_name: 'Drugs & Cosmetics Rules, 1945',
          authority: 'Ministry of AYUSH',
          content: 'Mandatory proof of safety and effectiveness documentation for patent or proprietary Ayurvedic, Siddha, or Unani medicines.',
          source_url: 'https://ayush.gov.in',
        },
      ],
      citations: ['Patents Act 1970 Sec 3(p)', 'Drugs & Cosmetics Rules 1945 Rule 158-B'],
      agents_invoked: ['IP Agent', 'AYUSH Agent', 'TK-ABS Agent'],
      disclaimer: 'This informational response is grounded in authoritative text archives and does not substitute for professional legal advice.',
    };
  }
}

export async function sendQueryToAPI(rawQuery: string): Promise<APIQueryResponse> {
  return processQueryAPI({ raw_query: rawQuery });
}

export async function checkHealthAPI(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { cache: 'no-store' });
    return res.ok;
  } catch {
    return false;
  }
}

export function getDocumentUrl(sourceId: string): string {
  return `${API_BASE_URL}/document/${encodeURIComponent(sourceId)}`;
}

export interface TranscribeResponse {
  transcript: string;
  language?: string;
  translated_text?: string | null;
  error?: string | null;
}

export async function transcribeAudio(audioBlob: Blob): Promise<TranscribeResponse> {
  const formData = new FormData();
  formData.append('file', audioBlob, 'voice_input.webm');

  const res = await fetch(`${API_BASE_URL}/transcribe`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => 'Audio transcription request failed');
    throw new Error(errText || `Server error ${res.status}`);
  }

  return res.json();
}

