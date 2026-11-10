import { BookOpen } from 'lucide-react';
import type { CitationRef } from '../types';

interface CitationCardProps {
  citation: CitationRef;
  index?: number;
}

export default function CitationCard({ citation, index }: CitationCardProps) {
  return (
    <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-800/50 border border-slate-700/50 hover:border-slate-600/50 transition-colors">
      <BookOpen size={20} className="text-blue-400 shrink-0 mt-1" />
      <div className="min-w-0 flex-1">
        <p className="text-blue-300 font-medium truncate">{citation.doc_title}</p>
        <p className="text-slate-400 text-xs mt-1">
          {citation.article && <span>Art. {citation.article} · </span>}
          p.{citation.page}
          {index !== undefined && (
            <span className="ml-2 text-slate-500">[{index + 1}]</span>
          )}
        </p>
        {citation.snippet && (
          <p className="text-slate-300 mt-2 italic text-sm line-clamp-2">
            « {citation.snippet} »
          </p>
        )}
        <div className="mt-2 flex items-center gap-2">
          <div className="w-20 h-1.5 bg-slate-700 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
              style={{ width: `${citation.relevance_score * 100}%` }}
            />
          </div>
          <span className="text-xs text-slate-500">
            Pertinence: {(citation.relevance_score * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    </div>
  );
}
