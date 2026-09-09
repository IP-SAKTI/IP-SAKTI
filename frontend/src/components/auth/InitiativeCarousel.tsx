'use client';

import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export interface SlideData {
  id: string;
  title: string;
  image: string;
}

const CAROUSEL_SLIDES: SlideData[] = [
  {
    id: 'patent-prior-art',
    title: 'Patents for People\'s Wellbeing',
    image: '/assests/ip-sakti/carousel/patent-prior-art.png',
  },
  {
    id: 'ayush-regulation',
    title: 'AYUSH Regulation & Compliance',
    image: '/assests/ip-sakti/carousel/ayush-regulation.png',
  },
  {
    id: 'access-benefit-sharing',
    title: 'Access & Benefit Sharing',
    image: '/assests/ip-sakti/carousel/access-benefit-sharing.png',
  },
  {
    id: 'regulatory-insights',
    title: 'Regulatory Insights',
    image: '/assests/ip-sakti/carousel/regulatory-insights.png',
  },
];

export default function InitiativeCarousel() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isHovered, setIsHovered] = useState(false);

  useEffect(() => {
    if (isHovered) return;
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % CAROUSEL_SLIDES.length);
    }, 6000);
    return () => clearInterval(timer);
  }, [isHovered]);

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % CAROUSEL_SLIDES.length);
  };

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + CAROUSEL_SLIDES.length) % CAROUSEL_SLIDES.length);
  };

  return (
    <div
      className="w-full relative space-y-2 font-sans-body"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Viewport: Controlled height ~250px–275px for 1440px desktop viewport */}
      <div className="w-full h-[240px] sm:h-[265px] md:h-[275px] rounded-2xl border border-[#D4DEC9] overflow-hidden bg-[#FAF8F1] shadow-xs relative">
        {/* Sliding Track */}
        <div
          className="flex transition-transform duration-500 ease-in-out w-full h-full"
          style={{ transform: `translateX(-${currentSlide * 100}%)` }}
        >
          {CAROUSEL_SLIDES.map((slide) => (
            <div key={slide.id} className="w-full h-full shrink-0 flex-none relative">
              <img
                src={slide.image}
                alt={slide.title}
                className="w-full h-full object-cover object-center rounded-2xl block"
              />
            </div>
          ))}
        </div>

        {/* Navigation Arrows */}
        <button
          onClick={prevSlide}
          aria-label="Previous slide"
          className="absolute left-2.5 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-white/85 hover:bg-white text-[#064E3B] border border-[#C8D7C2] flex items-center justify-center shadow-md transition-all z-20 cursor-pointer"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        <button
          onClick={nextSlide}
          aria-label="Next slide"
          className="absolute right-2.5 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-white/85 hover:bg-white text-[#064E3B] border border-[#C8D7C2] flex items-center justify-center shadow-md transition-all z-20 cursor-pointer"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Pagination Dots (4 Dots for 4 Slides) */}
      <div className="flex items-center justify-center gap-1.5 pt-0.5">
        {CAROUSEL_SLIDES.map((_, idx) => (
          <button
            key={idx}
            onClick={() => setCurrentSlide(idx)}
            className={`h-1.5 rounded-full transition-all cursor-pointer ${
              currentSlide === idx ? 'w-5 bg-[#064E3B]' : 'w-1.5 bg-[#C8D7C2] hover:bg-[#064E3B]/50'
            }`}
            aria-label={`Go to slide ${idx + 1}`}
          />
        ))}
      </div>
    </div>
  );
}
