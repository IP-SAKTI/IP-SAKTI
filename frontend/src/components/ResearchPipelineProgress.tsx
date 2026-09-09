'use client';

import React from 'react';
import { CheckCircle2, Loader2, Circle } from 'lucide-react';

export interface Stage {
  id: string;
  label: string;
  status: 'pending' | 'processing' | 'complete';
}

interface ResearchPipelineProgressProps {
  stages: Stage[];
}

export default function ResearchPipelineProgress({ stages }: ResearchPipelineProgressProps) {
  return (
    <div className="bg-[#FAFDF6] border border-[#C8D7C2] rounded-xl p-4 my-4 shadow-sm relative z-10">
      <div className="text-xs font-semibold text-[#003E29] uppercase tracking-wider mb-3 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-[#003E29] animate-pulse"></span>
        <span>Research Pipeline Active</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
        {stages.map((stage) => {
          return (
            <div
              key={stage.id}
              className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                stage.status === 'complete'
                  ? 'bg-emerald-50 text-emerald-900 border-emerald-200'
                  : stage.status === 'processing'
                  ? 'bg-amber-50 text-amber-900 border-amber-300 animate-pulse'
                  : 'bg-gray-50 text-gray-500 border-gray-200'
              }`}
            >
              {stage.status === 'complete' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />}
              {stage.status === 'processing' && <Loader2 className="w-3.5 h-3.5 text-amber-600 animate-spin shrink-0" />}
              {stage.status === 'pending' && <Circle className="w-3.5 h-3.5 text-gray-400 shrink-0" />}
              <span className="truncate">{stage.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
