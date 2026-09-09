'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowLeft, GitCompare, FileText, Download, Share2, Filter, Search } from 'lucide-react';
import HeaderUserProfile from '@/components/HeaderUserProfile';
import { useAuth } from '@/context/AuthContext';

export default function ComparePage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const [selectedJurisdictions, setSelectedJurisdictions] = useState(['India', 'Europe', 'USA']);
  const [filterQuery, setFilterQuery] = useState('');

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#001D14] flex items-center justify-center text-white text-sm font-sans-body">
        Loading IP-SAKTI...
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-[#001D14] flex items-center justify-center text-white text-sm font-sans-body">
        Loading IP-SAKTI...
      </div>
    );
  }

  const matrix = [
    {
      domain: 'Patentability Exclusions on TK',
      india: 'Section 3(p) of Patents Act 1970 expressly bars Traditional Knowledge aggregations and known component duplications.',
      ep: 'Article 53(a) public order & Article 54 prior art disclosures. Requires novelty over documented TKDL references.',
      us: '35 U.S.C. 102 prior art disclosures. No specific TK exclusion clause; relies on general non-obviousness.',
      wipo: 'Intergovernmental Committee (IGC) draft articles on TK protection & mandatory disclosure recommendations.',
    },
    {
      domain: 'Access & Benefit Sharing (ABS)',
      india: 'Mandatory approval from National Biodiversity Authority (NBA) under Biological Diversity Act 2002 (Sec 6).',
      ep: 'EU ABS Regulation (No 511/2014) implementing Nagoya Protocol. Mandatory due diligence declaration.',
      us: 'Not a party to the Convention on Biological Diversity (CBD) or Nagoya Protocol. No federal ABS mandate.',
      wipo: 'WIPO Treaty on Intellectual Property, Genetic Resources and Associated Traditional Knowledge (2024).',
    },
    {
      domain: 'AYUSH / Botanical Drug Regulations',
      india: 'Drugs & Cosmetics Rules 1945 Rule 158-B proof of safety & clinical data for patent/proprietary ASU medicines.',
      ep: 'Traditional Herbal Medicinal Products Directive 2004/24/EC (THMPD) requiring 30 years medicinal use.',
      us: 'FDA Botanical Drug Development Guidance for Industry (NDA route with standardized botanical batch control).',
      wipo: 'WHO Guidelines on Good Agricultural and Collection Practices (GACP) for Medicinal Plants.',
    },
  ];

  const filteredMatrix = matrix.filter((row) =>
    row.domain.toLowerCase().includes(filterQuery.toLowerCase()) ||
    row.india.toLowerCase().includes(filterQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen w-full bg-[#EEF3E4] font-sans-body relative flex flex-col p-6 lg:p-12">
      {/* Header */}
      <header className="max-w-6xl w-full mx-auto flex items-center justify-between mb-8 relative z-20">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-xs font-semibold text-[#003E29] bg-white border border-[#C8D7C2] px-3.5 py-2 rounded-lg hover:bg-[#FAFDF6] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Research Dashboard</span>
        </Link>

        <HeaderUserProfile />
      </header>

      {/* Main Legal Matrix Workspace */}
      <main className="max-w-6xl w-full mx-auto bg-white border border-[#C8D7C2] rounded-2xl p-8 lg:p-10 shadow-sm relative z-10 space-y-6">
        <div className="border-b border-[#C8D7C2]/80 pb-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 bg-[#EEF3E4] text-[#003E29] text-xs font-bold px-3 py-1 rounded-md mb-2">
              <GitCompare className="w-3.5 h-3.5" />
              <span>Comparative Legal Matrix</span>
            </div>
            <h1 className="font-serif-heading text-3xl lg:text-4xl font-bold text-[#003E29]">
              Cross-Jurisdiction IP, ABS & Regulatory Matrix
            </h1>
            <p className="text-xs text-[#385246] mt-1">
              Comparative analysis across India (IPO/NBA), European Patent Office (EPO), US Patent Office (USPTO), and WIPO treaties.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button className="flex items-center gap-1.5 bg-[#EEF3E4] hover:bg-[#E3EBD7] text-[#003E29] text-xs font-semibold px-3 py-2 rounded-lg border border-[#C8D7C2] transition-colors cursor-pointer">
              <Share2 className="w-3.5 h-3.5" />
              <span>Share</span>
            </button>
            <button className="flex items-center gap-1.5 bg-[#003E29] hover:bg-[#044D34] text-white text-xs font-semibold px-3.5 py-2 rounded-lg shadow-sm transition-colors cursor-pointer">
              <Download className="w-3.5 h-3.5" />
              <span>Export Matrix PDF</span>
            </button>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-[#FAFDF6] border border-[#C8D7C2] rounded-xl p-4 text-xs">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-[#385246]" />
            <input
              type="text"
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              placeholder="Search legal provisions, ABS rules, or prior art..."
              className="w-full bg-white border border-[#C8D7C2] rounded-lg pl-9 pr-3 py-2 text-xs text-[#003E29] placeholder-[#7C817A] focus:outline-none focus:border-[#003E29]"
            />
          </div>

          <div className="flex items-center gap-2 text-[#003E29] font-medium">
            <Filter className="w-3.5 h-3.5" />
            <span>Active Jurisdictions:</span>
            <span className="bg-[#EEF3E4] border border-[#C8D7C2] px-2 py-0.5 rounded font-bold">🇮🇳 India</span>
            <span className="bg-[#EEF3E4] border border-[#C8D7C2] px-2 py-0.5 rounded font-bold">🇪🇺 Europe</span>
            <span className="bg-[#EEF3E4] border border-[#C8D7C2] px-2 py-0.5 rounded font-bold">🇺🇸 USA</span>
            <span className="bg-[#EEF3E4] border border-[#C8D7C2] px-2 py-0.5 rounded font-bold">🌐 WIPO</span>
          </div>
        </div>

        {/* Matrix Table */}
        <div className="border border-[#C8D7C2] rounded-xl overflow-hidden text-xs shadow-xs">
          <table className="w-full text-left">
            <thead className="bg-[#003E29] text-white font-bold">
              <tr>
                <th className="p-4 w-1/5 border-r border-[#044D34]">Legal Domain / Provision</th>
                <th className="p-4 w-1/5 border-r border-[#044D34]">🇮🇳 India (IPO / NBA / AYUSH)</th>
                <th className="p-4 w-1/5 border-r border-[#044D34]">🇪🇺 Europe (EPO / EU)</th>
                <th className="p-4 w-1/5 border-r border-[#044D34]">🇺🇸 USA (USPTO / FDA)</th>
                <th className="p-4 w-1/5">🌐 WIPO / International</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#C8D7C2]/60 text-[#1A2E26]">
              {filteredMatrix.map((row, idx) => (
                <tr key={idx} className="hover:bg-[#FAFDF6]">
                  <td className="p-4 font-bold text-[#003E29] bg-[#EEF3E4]/40 border-r border-[#C8D7C2]/60">{row.domain}</td>
                  <td className="p-4 leading-relaxed font-medium border-r border-[#C8D7C2]/60">{row.india}</td>
                  <td className="p-4 leading-relaxed border-r border-[#C8D7C2]/60">{row.ep}</td>
                  <td className="p-4 leading-relaxed border-r border-[#C8D7C2]/60">{row.us}</td>
                  <td className="p-4 leading-relaxed">{row.wipo}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
