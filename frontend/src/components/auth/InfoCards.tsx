'use client';

import React from 'react';
import { ArrowRight } from 'lucide-react';

export default function InfoCards() {
  const cards = [
    {
      id: '1',
      title: 'AYUSH for a Healthier Bharat',
      copy: 'Supporting safe, standardised AYUSH practices through evidence-based research.',
      image: '/assests/ip-sakti/carousel/ayush-regulation.png',
    },
    {
      id: '2',
      title: 'Access & Benefit Sharing',
      copy: 'Promoting fair and responsible use of India\'s bio-resources.',
      image: '/assests/ip-sakti/carousel/access-benefit-sharing.png',
    },
    {
      id: '3',
      title: 'Regulatory Insights',
      copy: 'Simplifying policy, compliance and global requirements for informed decision-making.',
      image: '/assests/ip-sakti/carousel/regulatory-insights.png',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-sans-body">
      {cards.map((card) => (
        <div
          key={card.id}
          className="bg-[#FAF8F1] border border-[#D4DEC9] rounded-xl overflow-hidden shadow-xs flex flex-col justify-between hover:shadow-md transition-all group"
        >
          {/* Image Thumbnail */}
          <div className="h-28 w-full relative overflow-hidden bg-[#064E3B]/5">
            <img
              src={card.image}
              alt={card.title}
              className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-300"
            />
          </div>

          {/* Card Content */}
          <div className="p-4 flex-1 flex flex-col justify-between space-y-2">
            <div>
              <h4 className="font-serif-heading font-bold text-sm text-[#064E3B] leading-snug">
                {card.title}
              </h4>
              <p className="text-xs text-[#385246] leading-relaxed mt-1">
                {card.copy}
              </p>
            </div>

            <div className="pt-2">
              <button
                onClick={() => alert(`Exploring ${card.title}`)}
                className="w-7 h-7 rounded-full bg-white border border-[#D4DEC9] flex items-center justify-center text-[#064E3B] hover:bg-[#064E3B] hover:text-white transition-colors cursor-pointer"
                aria-label={`Learn more about ${card.title}`}
              >
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
