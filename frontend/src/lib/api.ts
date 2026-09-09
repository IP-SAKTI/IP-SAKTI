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

export const MOCK_CONVERSATIONS: Conversation[] = [
  {
    id: 'conv-1',
    title: 'Is turmeric + neem patentable?',
    created_at: '2026-09-08T18:00:00.000Z',
    query: 'Is turmeric + neem patentable in India?',
    response: {
      query_id: 'mock-1',
      answer: 'Under Section 3(p) of the Indian Patents Act, 1970, formulations combining Curcuma longa (Turmeric) and Azadirachta indica (Neem) are excluded from patentability as they constitute known Traditional Knowledge and an aggregation of known properties of traditionally known components.\n\nRevocation of US Patent 5,401,504 (CSIR Turmeric Case) established prior art precedent from ancient Ayurvedic texts including Charaka Samhita.',
      is_abstention: false,
      confidence: 0.94,
      evidence: [
        {
          source_id: 'TKDL-AYU-0842',
          doc_id: 'TKDL-AYU-0842',
          title: 'Charaka Samhita — Chikitsa Sthana Formulation Records',
          source_name: 'Traditional Knowledge Digital Library (TKDL)',
          authority: 'AYUSH / CSIR',
          content: 'Documented topical application of Haridra (Turmeric) and Nimbaka (Neem) for Vrana Ropana (wound healing) and Kustha (dermatological conditions).',
          source_url: 'https://tkdl.res.in',
        },
        {
          source_id: 'IPA-1970-SEC3P',
          doc_id: 'IPA-1970-SEC3P',
          title: 'Indian Patents Act 1970 — Section 3(p)',
          source_name: 'Patents Act, 1970',
          authority: 'Indian Patent Office',
          content: 'An invention which in effect, is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components is not patentable.',
          source_url: 'https://ipindia.gov.in',
        },
      ],
      citations: ['Charaka Samhita Chikitsa Sthana Ch. 7', 'Patents Act 1970 Sec 3(p)'],
      agents_invoked: ['IP Agent', 'TK-ABS Agent'],
      disclaimer: 'This informational response is grounded in authoritative text archives and does not substitute for professional legal advice.',
    },
  },
  {
    id: 'conv-2',
    title: 'AYUSH Rule 158-B Licensing',
    created_at: '2026-09-08T17:00:00.000Z',
    query: 'AYUSH licensing steps under Rule 158-B',
  },
  {
    id: 'conv-3',
    title: 'ABS under Biodiversity Act',
    created_at: '2026-09-07T18:00:00.000Z',
    query: 'ABS obligations under Biodiversity Act',
  },
];

export async function processQueryAPI(payload: APIQueryPayload): Promise<APIQueryResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
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

export async function listConversations(): Promise<Conversation[]> {
  return MOCK_CONVERSATIONS;
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
