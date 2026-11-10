import { useCallback, useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, FileSearch, Eye } from 'lucide-react';
import { api } from '../services/api';
import type { DocumentRecord } from '../types';

interface DocumentsPageProps {
  activeCaseId: string | null;
}

export default function DocumentsPage({ activeCaseId }: DocumentsPageProps) {
  const [docs, setDocs] = useState<DocumentRecord[]>([]);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const upload = useCallback(
    async (file: File) => {
      if (!activeCaseId) { setError('Sélectionnez d\'abord un dossier.'); return; }
      setUploading(true);
      setError(null);
      try {
        const doc = await api.uploadDocument(activeCaseId, file);
        setDocs(prev => [doc, ...prev]);
      } catch (e) {
        setError(String(e));
      } finally {
        setUploading(false);
      }
    },
    [activeCaseId],
  );

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) upload(file);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) upload(file);
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="animate-fadeIn">
        <h1 className="text-3xl font-bold gradient-text">Documents</h1>
        <p className="text-slate-400 mt-2">
          {activeCaseId
            ? `Dossier actif : ${activeCaseId.slice(0, 8)}…`
            : 'Aucun dossier sélectionné — ouvrez un dossier depuis le tableau de bord.'}
        </p>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-2xl p-12 flex flex-col items-center gap-4 cursor-pointer transition-all duration-300 animate-slideIn
          ${dragging ? 'border-blue-500 bg-blue-950/50 scale-105' : 'border-slate-600 hover:border-slate-500 hover:bg-slate-800/50'}`}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <div className={`p-4 rounded-xl ${dragging ? 'bg-blue-600' : 'bg-slate-800'}`}>
          <Upload size={32} className={dragging ? 'text-white' : 'text-slate-400'} />
        </div>
        <div className="text-center">
          <p className="text-slate-300 font-medium text-lg">
            {uploading ? 'Upload en cours…' : 'Glissez un document ici ou cliquez'}
          </p>
          <p className="text-slate-500 text-sm mt-1">PDF, JPEG, PNG, TXT — Permis, RI, Carte Grise, Attestation…</p>
        </div>
        <input id="file-input" type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png,.txt"
          onChange={handleChange} />
      </div>

      {error && (
        <div className="p-4 bg-red-950/50 border border-red-700/50 rounded-xl text-red-300 flex items-center gap-3">
          <AlertCircle size={20} /> {error}
        </div>
      )}

      {/* Document list */}
      {docs.length > 0 && (
        <div className="card overflow-hidden animate-fadeIn">
          <div className="px-6 py-4 border-b border-slate-700/50 flex items-center gap-3">
            <FileSearch size={20} className="text-blue-400" />
            <span className="font-semibold text-slate-200 text-lg">Documents traités ({docs.length})</span>
          </div>
          <div className="divide-y divide-slate-800/50">
            {docs.map(doc => (
              <div key={doc.id} className="p-6 space-y-4 hover:bg-slate-800/30 transition-colors">
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-xl bg-slate-800/50">
                    <FileText size={24} className="text-blue-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-slate-200 text-lg truncate">{doc.filename}</p>
                    <div className="flex items-center gap-3 mt-2">
                      <span className="text-xs bg-blue-900/50 text-blue-300 px-3 py-1 rounded-full border border-blue-700/50">
                        {doc.doc_label || doc.doc_type}
                      </span>
                      <span className={`text-xs px-3 py-1 rounded-full border ${
                        doc.ocr_status === 'completed'
                          ? 'bg-emerald-900/50 text-emerald-300 border-emerald-700/50'
                          : 'bg-amber-900/50 text-amber-300 border-amber-700/50'
                      }`}>
                        {doc.ocr_status}
                      </span>
                      {doc.page_count > 0 && (
                        <span className="text-xs text-slate-400">{doc.page_count} page(s)</span>
                      )}
                    </div>
                  </div>
                  {doc.confidence > 0.8 && (
                    <CheckCircle size={24} className="text-emerald-400 shrink-0" />
                  )}
                </div>

                {/* Extracted fields */}
                {doc.extracted_fields && doc.extracted_fields.length > 0 && (
                  <div className="ml-16">
                    <p className="text-sm text-slate-400 mb-3 flex items-center gap-2">
                      <Eye size={16} /> Champs extraits
                    </p>
                    <div className="grid grid-cols-2 gap-3">
                      {doc.extracted_fields.map((field, i) => (
                        <div key={i} className="bg-slate-800/50 rounded-xl px-4 py-3">
                          <p className="text-xs text-slate-400 mb-1">{field.label}</p>
                          <div className="flex items-center justify-between">
                            <span className="text-slate-200 font-mono text-sm">{String(field.value)}</span>
                            <span className="text-slate-500 text-xs">
                              {(field.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="mt-2 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
                              style={{ width: `${field.confidence * 100}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
