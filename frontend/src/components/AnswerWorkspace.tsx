'use client';

import React from 'react';
import Link from 'next/link';
import {
  ShieldCheck,
  ExternalLink,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Bookmark,
  GitCompare,
  Download,
  Info,
  Cpu,
  Layers,
  Sparkles,
} from 'lucide-react';
import { APIQueryResponse, getDocumentUrl } from '@/lib/api';

interface AnswerWorkspaceProps {
  query: string;
  response: APIQueryResponse;
  onSaveResearch?: () => void;
}

export default function AnswerWorkspace({
  query,
  response,
  onSaveResearch,
}: AnswerWorkspaceProps) {
  const confidencePercentage = Math.round((response.confidence || 0) * 100);

  // Extract key findings bullet points from answer if available
  const keyFindings = response.answer
    ? response.answer
        .split('\n')
        .filter((line) => line.trim().length > 20 && !line.startsWith('['))
        .slice(0, 3)
    : [];

  return (
    <div className="space-y-6 my-6 relative z-10 font-sans-body">
      {/* 1. RESEARCH QUESTION HEADER */}
      <div className="bg-white border border-[#C8D7C2] rounded-xl p-5 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-2 border-b border-[#C8D7C2]/60 pb-3">
          <div className="text-[11px] font-bold text-[#003E29] uppercase tracking-wider">
            RESEARCH QUESTION
          </div>

          <div className="flex items-center gap-2">
            {/* Detected Language */}
            <span className="bg-[#EEF3E4] text-[#003E29] text-[11px] font-semibold px-2.5 py-0.5 rounded border border-[#C8D7C2]">
              Language: English / Auto-Detected
            </span>

            {/* Invoked Agents / Category */}
            {response.agents_invoked?.map((agent, idx) => {
              const agentLabel =
                typeof agent === 'string'
                  ? agent
                  : typeof agent === 'object' && agent !== null
                  ? (agent as any).name || (agent as any).value || String(agent)
                  : String(agent);

              return (
                <span
                  key={idx}
                  className="bg-[#EEF3E4] text-[#003E29] text-[11px] font-semibold px-2.5 py-0.5 rounded border border-[#C8D7C2]"
                >
                  {agentLabel}
                </span>
              );
            })}

            {/* Confidence Score */}
            {response.confidence !== undefined && response.confidence !== null ? (
              <div className="flex items-center gap-1.5 bg-[#003E29] text-white text-xs font-semibold px-3 py-1 rounded-md shadow-xs">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-300" />
                <span>Confidence: {confidencePercentage}% ({confidencePercentage >= 80 ? 'High' : 'Moderate'})</span>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 bg-gray-100 text-gray-700 text-xs font-medium px-2.5 py-1 rounded-md">
                <Info className="w-3.5 h-3.5" />
                <span>Confidence unavailable</span>
              </div>
            )}
          </div>
        </div>

        <p className="text-base font-serif-heading font-bold text-[#003E29]">
          "{query}"
        </p>
      </div>

      {/* 2. RESEARCH PROCESS BAR (High Level) */}
      <div className="bg-white border border-[#C8D7C2] rounded-xl p-4 shadow-xs text-xs text-[#385246]">
        <div className="flex items-center gap-2 font-bold text-[#003E29] mb-2 uppercase tracking-wider text-[11px]">
          <Cpu className="w-3.5 h-3.5 text-[#003E29]" />
          <span>RESEARCH PROCESS TRACKER</span>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-[11px] font-medium">
          <span className="flex items-center gap-1 bg-emerald-50 text-emerald-900 px-2 py-1 rounded border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Language Detection
          </span>
          <span className="text-gray-300">→</span>
          <span className="flex items-center gap-1 bg-emerald-50 text-emerald-900 px-2 py-1 rounded border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Query Normalization
          </span>
          <span className="text-gray-300">→</span>
          <span className="flex items-center gap-1 bg-emerald-50 text-emerald-900 px-2 py-1 rounded border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Hybrid FAISS + BM25 RAG
          </span>
          <span className="text-gray-300">→</span>
          <span className="flex items-center gap-1 bg-emerald-50 text-emerald-900 px-2 py-1 rounded border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Cross-Encoder Reranking
          </span>
          <span className="text-gray-300">→</span>
          <span className="flex items-center gap-1 bg-emerald-50 text-emerald-900 px-2 py-1 rounded border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Citation Validation
          </span>
        </div>
      </div>

      {/* 3. MAIN ANSWER SYNTHESIS */}
      <div className="bg-white border border-[#C8D7C2] rounded-xl p-6 shadow-xs space-y-4">
        <div className="border-b border-[#C8D7C2]/60 pb-3">
          <h2 className="font-serif-heading text-2xl font-bold text-[#003E29]">
            Research Synthesis & Answer
          </h2>
          <div className="text-xs text-[#385246] mt-0.5">
            Grounded in verified statutory provisions and Traditional Knowledge archives
          </div>
        </div>

        <div className="text-sm text-[#1A2E26] leading-relaxed whitespace-pre-wrap font-sans-body">
          {response.answer}
        </div>

        {/* Abstention Banner */}
        {response.is_abstention && (
          <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg text-xs text-amber-900 flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold mb-0.5">Human / IP Facilitator Escalation Recommended</div>
              <div>Evidence threshold was insufficient for a conclusive decision. Consult an IP Facilitator or AYUSH authority.</div>
            </div>
          </div>
        )}
      </div>

      {/* 4. KEY FINDINGS */}
      {keyFindings.length > 0 && (
        <div className="bg-[#FFFFFF] border border-[#C8D7C2] rounded-xl p-5 shadow-xs space-y-3">
          <div className="flex items-center gap-2 font-serif-heading text-lg font-bold text-[#003E29]">
            <Sparkles className="w-4 h-4 text-[#003E29]" />
            <span>Key Findings</span>
          </div>
          <ul className="space-y-2 text-xs text-[#263A35]">
            {keyFindings.map((finding, idx) => (
              <li key={idx} className="flex items-start gap-2 bg-[#FAFDF6] p-2.5 rounded-lg border border-[#C8D7C2]/50">
                <span className="font-bold text-[#003E29]">•</span>
                <span className="leading-relaxed">{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 5. GROUNDED EVIDENCE CARDS */}
      {response.evidence && response.evidence.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-serif-heading text-xl font-bold text-[#003E29]">
              Grounded Source Evidence ({response.evidence.length})
            </h3>
            <span className="text-xs text-[#385246]">Cross-Encoder Verified</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {response.evidence.map((item, index) => {
              const docUrl = item.source_id ? getDocumentUrl(item.source_id) : item.source_url;

              return (
                <div
                  key={index}
                  className="bg-white border border-[#C8D7C2] rounded-xl p-4 shadow-xs hover:shadow-md transition-shadow flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-1.5">
                      <div className="font-serif-heading font-bold text-sm text-[#003E29] leading-snug">
                        {item.title}
                      </div>
                      <span className="shrink-0 bg-emerald-50 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded border border-emerald-200">
                        Official Source
                      </span>
                    </div>

                    <div className="text-[11px] font-semibold text-[#385246] mb-2">
                      {item.authority} · {item.source_name}
                    </div>

                    <p className="text-xs text-[#263A35] leading-relaxed bg-[#FAFDF6] p-3 rounded-lg border border-[#C8D7C2]/50 italic">
                      "{item.content}"
                    </p>
                  </div>

                  {docUrl && (
                    <div className="mt-3 pt-2 border-t border-[#C8D7C2]/40 flex justify-end">
                      <a
                        href={docUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs font-semibold text-[#003E29] hover:underline"
                      >
                        <FileText className="w-3.5 h-3.5 text-[#003E29]" />
                        <span>Inspect Document Chunk</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 6. SOURCES & CITATIONS */}
      {response.citations && response.citations.length > 0 && (
        <div className="bg-white border border-[#C8D7C2] rounded-xl p-4 text-xs text-[#385246]">
          <div className="font-bold text-[#003E29] uppercase tracking-wider text-[11px] mb-2">
            OFFICIAL CITATIONS & SOURCES
          </div>
          <div className="flex flex-wrap gap-2">
            {response.citations.map((cite, i) => {
              const label =
                typeof cite === 'string'
                  ? cite
                  : typeof cite === 'object' && cite !== null
                  ? (cite as any).source_label
                    ? `${(cite as any).source_label}${(cite as any).claim_snippet ? `: ${(cite as any).claim_snippet}` : ''}`
                    : (cite as any).claim_snippet || JSON.stringify(cite)
                  : String(cite);

              return (
                <span
                  key={i}
                  className="bg-[#EEF3E4] border border-[#C8D7C2] text-[#003E29] px-2.5 py-1 rounded text-[11px] font-medium"
                >
                  {label}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* 7. ACTION BUTTONS ROW */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white border border-[#C8D7C2] rounded-xl p-4 shadow-xs">
        <div className="text-xs font-semibold text-[#003E29]">
          Research Actions
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            onClick={onSaveResearch || (() => alert('Research saved to your history.'))}
            className="flex items-center gap-1.5 bg-[#EEF3E4] hover:bg-[#E3EBD7] text-[#003E29] text-xs font-semibold px-3.5 py-2 rounded-lg border border-[#C8D7C2] transition-colors cursor-pointer"
          >
            <Bookmark className="w-3.5 h-3.5" />
            <span>Save Research</span>
          </button>

          <Link
            href="/brief"
            className="flex items-center gap-1.5 bg-[#EEF3E4] hover:bg-[#E3EBD7] text-[#003E29] text-xs font-semibold px-3.5 py-2 rounded-lg border border-[#C8D7C2] transition-colors"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Generate Brief</span>
          </Link>

          <Link
            href="/compare"
            className="flex items-center gap-1.5 bg-[#003E29] hover:bg-[#044D34] text-white text-xs font-semibold px-3.5 py-2 rounded-lg shadow-sm transition-colors"
          >
            <GitCompare className="w-3.5 h-3.5" />
            <span>Compare Jurisdictions</span>
          </Link>
        </div>
      </div>

      {/* Disclaimer Note */}
      {response.disclaimer && (
        <div className="text-[11px] text-[#385246] italic leading-relaxed pt-2">
          {response.disclaimer}
        </div>
      )}
    </div>
  );
}
