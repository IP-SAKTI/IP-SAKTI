'use client';

import React from 'react';
import { Search, Shield, FileText, ArrowRight } from 'lucide-react';

interface FeatureCardsProps {
  onSelectQuery: (query: string) => void;
}

export default function FeatureCards({ onSelectQuery }: FeatureCardsProps) {
  const cards = [
    {
      id: 'prior-art',
      title: 'Prior Art Inquiry',
      copy: 'Explore patent prior art, exclusions and Traditional Knowledge references.',
      query: 'Is turmeric + neem patentable in India?',
      icon: Search,
    },
    {
      id: 'ayush-compliance',
      title: 'AYUSH Compliance',
      copy: 'Examine regulatory requirements and formulation-specific considerations.',
      query: 'AYUSH licensing steps under Rule 158-B',
      icon: FileText,
    },
    {
      id: 'abs-consent',
      title: 'ABS & Consent',
      copy: 'Examine Access & Benefit-Sharing obligations and relevant biological-resource provisions.',
      query: 'ABS obligations under Biodiversity Act',
      icon: Shield,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-6 relative z-10">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <button
            key={card.id}
            onClick={() => onSelectQuery(card.query)}
            className="group text-left bg-white hover:bg-[#FAFDF6] border border-[#C8D7C2] border-l-4 border-l-[#003E29] rounded-xl p-5 shadow-xs hover:shadow-md transition-all duration-200 active:scale-[0.99] flex flex-col justify-between cursor-pointer"
          >
            <div>
              <div className="flex items-center gap-2.5 mb-2.5">
                <div className="shrink-0 p-1.5 bg-[#EEF3E4] rounded-lg group-hover:bg-[#E3EBD7] transition-colors">
                  <Icon className="w-4 h-4 text-[#003E29]" />
                </div>
                <h3 className="font-serif-heading text-lg font-bold text-[#003E29] group-hover:text-[#044D34] transition-colors">
                  {card.title}
                </h3>
              </div>
              <p className="font-sans-body text-xs text-[#385246] leading-relaxed">
                {card.copy}
              </p>
            </div>

            <div className="text-[11px] font-semibold text-[#003E29] opacity-70 group-hover:opacity-100 transition-opacity mt-4 flex items-center gap-1.5">
              <span>Run research inquiry</span>
              <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
            </div>
          </button>
        );
      })}
    </div>
  );
}
