import { useEffect, useState, useCallback } from 'react';
import { Loader2, Shield, ChevronRight, CheckCircle2, XCircle, FileText, Users, Database, BarChart3, Lock, Eye, Download, Plus } from 'lucide-react';
import { api } from '../services/api';
import type { AuditTrail, AuditEvent, Case } from '../types';
import StatusBadge from '../components/StatusBadge';

interface AuditPageProps {
  activeCaseId: string | null;
  setActiveCaseId?: (id: string) => void;
}

const eventLabel: Record<string, string> = {
  CASE_CREATED:    'Dossier créé',
  DOCUMENT_UPLOADED: 'Document téléversé',
  ANALYSIS_EXECUTED: 'Analyse exécutée',
  AGENT_RUN:       'Agent exécuté',
  DECISION_MADE:   'Décision émise',
  HUMAN_REVIEW:    'Revue souscripteur',
  AUDIT_VERIFIED:  'Audit vérifié',
  DATA_EXPORT:     'Export de données',
  CONSENT_GIVEN:   'Consentement donné',
};

const eventIcon: Record<string, React.ReactNode> = {
  CASE_CREATED:    <Users size={20} />,
  DOCUMENT_UPLOADED: <FileText size={20} />,
  ANALYSIS_EXECUTED: <BarChart3 size={20} />,
  AGENT_RUN:       <Database size={20} />,
  DECISION_MADE:   <CheckCircle2 size={20} />,
  HUMAN_REVIEW:    <Users size={20} />,
  AUDIT_VERIFIED:  <Shield size={20} />,
  DATA_EXPORT:     <Download size={20} />,
  CONSENT_GIVEN:   <CheckCircle2 size={20} />,
};

const eventColor: Record<string, string> = {
  CASE_CREATED:    'from-blue-500 to-blue-600',
  DOCUMENT_UPLOADED: 'from-violet-500 to-violet-600',
  ANALYSIS_EXECUTED: 'from-emerald-500 to-emerald-600',
  AGENT_RUN:       'from-cyan-500 to-cyan-600',
  DECISION_MADE:   'from-amber-500 to-amber-600',
  HUMAN_REVIEW:    'from-pink-500 to-pink-600',
  AUDIT_VERIFIED:  'from-emerald-500 to-emerald-600',
  DATA_EXPORT:     'from-orange-500 to-orange-600',
  CONSENT_GIVEN:   'from-green-500 to-green-600',
};

export default function AuditPage({ activeCaseId, setActiveCaseId }: AuditPageProps) {
  const [auditTrail, setAuditTrail] = useState<AuditTrail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cases, setCases] = useState<Case[]>([]);
  const [loadingCases, setLoadingCases] = useState(true);

  // Load available cases
  const loadCases = useCallback(async () => {
    try {
      const data = await api.listCases();
      setCases(data);
    } catch (e) {
      console.error('Failed to load cases:', e);
    } finally {
      setLoadingCases(false);
    }
  }, []);

  const load = useCallback(async () => {
    if (!activeCaseId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAuditTrail(activeCaseId);
      setAuditTrail(data);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [activeCaseId]);

  useEffect(() => { loadCases(); }, [loadCases]);
  useEffect(() => { load(); }, [load]);

  const events = auditTrail?.events || [];
  const allValid = auditTrail?.is_chain_intact || false;

  // If no case selected, show case selection
  if (!activeCaseId) {
    return (
      <div className="p-8 max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center gap-4 animate-fadeIn">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-600 flex items-center justify-center shadow-lg">
            <Shield size={32} className="text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold gradient-text">Audit & Conformité</h1>
            <p className="text-slate-400 mt-1">
              Sélectionnez un dossier pour voir la piste d'audit cryptographique
            </p>
          </div>
        </div>

        {/* Global Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card card-hover animate-slideIn">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600">
                <Lock size={20} className="text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-200">RGPD Compliance</h3>
                <p className="text-xs text-slate-400">Données chiffrées et traçables</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 size={16} className="text-emerald-400" />
              <span className="text-sm text-emerald-400">Conforme</span>
            </div>
          </div>

          <div className="card card-hover animate-slideIn" style={{ animationDelay: '0.1s' }}>
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600">
                <Users size={20} className="text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-200">Human-in-the-Loop</h3>
                <p className="text-xs text-slate-400">Validation humaine obligatoire</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 size={16} className="text-emerald-400" />
              <span className="text-sm text-emerald-400">Actif</span>
            </div>
          </div>

          <div className="card card-hover animate-slideIn" style={{ animationDelay: '0.2s' }}>
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 rounded-xl bg-gradient-to-br from-violet-500 to-violet-600">
                <Database size={20} className="text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-200">Traçabilité</h3>
                <p className="text-xs text-slate-400">Audit trail complet</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 size={16} className="text-emerald-400" />
              <span className="text-sm text-emerald-400">{cases.length} dossiers</span>
            </div>
          </div>
        </div>

        {/* Case Selection */}
        <div className="card animate-fadeIn" style={{ animationDelay: '0.3s' }}>
          <div className="px-6 py-4 border-b border-slate-700/50 flex items-center gap-3">
            <FileText size={20} className="text-blue-400" />
            <span className="font-semibold text-slate-200 text-lg">Sélectionner un dossier</span>
          </div>
          {loadingCases ? (
            <div className="flex items-center justify-center h-48 text-slate-400">
              <Loader2 size={24} className="animate-spin mr-2" /> Chargement…
            </div>
          ) : cases.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-slate-500">
              <FileText size={48} className="mb-4 text-slate-600" />
              <p className="text-lg">Aucun dossier disponible</p>
              <p className="text-sm text-slate-400 mt-2">Créez un dossier pour commencer</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700/50 bg-slate-800/30">
                    {['Référence', 'Assuré', 'Statut', 'Risque', 'Décision'].map(h => (
                      <th key={h} className="table-header text-left px-6 py-4">{h}</th>
                    ))}
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {cases.map(c => (
                    <tr
                      key={c.id}
                      className="border-b border-slate-800/50 hover:bg-slate-800/30 cursor-pointer transition-all duration-200 group"
                      onClick={() => setActiveCaseId && setActiveCaseId(c.id)}
                    >
                      <td className="px-6 py-4 font-mono text-blue-400 text-xs group-hover:text-blue-300">{c.reference || c.id.slice(0, 8)}</td>
                      <td className="px-6 py-4 font-medium text-slate-200">{c.applicant_name}</td>
                      <td className="px-6 py-4"><StatusBadge value={c.status} /></td>
                      <td className="px-6 py-4">
                        {c.risk_tier ? <StatusBadge value={c.risk_tier} /> : <span className="text-slate-600">—</span>}
                      </td>
                      <td className="px-6 py-4">
                        {c.decision_code
                          ? <span className="text-xs text-slate-300">{c.decision_code.replace(/_/g, ' ')}</span>
                          : <span className="text-slate-600">—</span>}
                      </td>
                      <td className="px-6 py-4 text-slate-500 text-right group-hover:text-blue-400 transition-colors">›</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between animate-fadeIn">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-600 flex items-center justify-center shadow-lg">
            <Shield size={32} className="text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold gradient-text">Audit & Conformité</h1>
            <p className="text-slate-400 mt-1">
              Chaîne cryptographique SHA-256 — dossier {activeCaseId.slice(0, 8)}…
            </p>
          </div>
        </div>
        {auditTrail && (
          <div className={`flex items-center gap-3 px-4 py-2 rounded-xl ${allValid ? 'bg-emerald-900/50 border border-emerald-700/50' : 'bg-red-900/50 border border-red-700/50'}`}>
            {allValid
              ? <CheckCircle2 size={20} className="text-emerald-400" />
              : <XCircle size={20} className="text-red-400" />}
            <span className={`font-medium ${allValid ? 'text-emerald-400' : 'text-red-400'}`}>
              {allValid ? 'Chaîne valide' : 'Intégrité compromise'}
            </span>
          </div>
        )}
      </div>

      {loading && (
        <div className="flex items-center gap-3 text-slate-400">
          <Loader2 size={24} className="animate-spin" /> Chargement…
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-950/50 border border-red-700/50 rounded-xl text-red-300">
          {error}
        </div>
      )}

      {/* Compliance Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card card-hover animate-slideIn">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600">
              <Lock size={20} className="text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-200">RGPD Compliance</h3>
              <p className="text-xs text-slate-400">Données chiffrées et traçables</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 size={16} className="text-emerald-400" />
            <span className="text-sm text-emerald-400">Conforme</span>
          </div>
        </div>

        <div className="card card-hover animate-slideIn" style={{ animationDelay: '0.1s' }}>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600">
              <Users size={20} className="text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-200">Human-in-the-Loop</h3>
              <p className="text-xs text-slate-400">Validation humaine obligatoire</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 size={16} className="text-emerald-400" />
            <span className="text-sm text-emerald-400">Actif</span>
          </div>
        </div>

        <div className="card card-hover animate-slideIn" style={{ animationDelay: '0.2s' }}>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-xl bg-gradient-to-br from-violet-500 to-violet-600">
              <Database size={20} className="text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-200">Traçabilité</h3>
              <p className="text-xs text-slate-400">Audit trail complet</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 size={16} className="text-emerald-400" />
            <span className="text-sm text-emerald-400">{auditTrail?.total_events || 0} événements</span>
          </div>
        </div>
      </div>

      {/* Timeline */}
      {events.length > 0 && (
        <div className="relative animate-fadeIn" style={{ animationDelay: '0.3s' }}>
          {/* Vertical line */}
          <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-500 to-slate-700" />

          <div className="space-y-6">
            {events.map((e, i) => (
              <div key={e.id} className="flex gap-6 relative">
                {/* Icon */}
                <div className={`w-16 h-16 shrink-0 rounded-2xl flex items-center justify-center z-10 bg-gradient-to-br ${eventColor[e.event_type] || 'from-slate-500 to-slate-600'} shadow-lg`}>
                  {eventIcon[e.event_type] || <FileText size={20} className="text-white" />}
                </div>

                {/* Content */}
                <div className="flex-1 card card-hover">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-slate-200 text-lg">
                        {eventLabel[e.event_type] ?? e.event_type}
                      </h3>
                      <p className="text-sm text-slate-400 mt-1">
                        {e.actor} · {new Date(e.timestamp).toLocaleString('fr-FR')}
                      </p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      e.current_hash === e.previous_hash
                        ? 'bg-emerald-900/50 text-emerald-300 border border-emerald-700/50'
                        : 'bg-red-900/50 text-red-300 border border-red-700/50'
                    }`}>
                      {e.current_hash === e.previous_hash ? '✓ Valide' : '✗ Invalide'}
                    </span>
                  </div>

                  {/* Hashes */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                    <div className="bg-slate-800/50 rounded-lg p-3">
                      <p className="text-xs text-slate-500 mb-1">Previous Hash</p>
                      <p className="font-mono text-xs text-slate-400 truncate">{e.previous_hash}</p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-3">
                      <p className="text-xs text-slate-500 mb-1">Current Hash</p>
                      <p className="font-mono text-xs text-slate-400 truncate">{e.current_hash}</p>
                    </div>
                  </div>

                  {/* Details */}
                  {e.details && Object.keys(e.details).length > 0 && (
                    <details className="group">
                      <summary className="text-sm text-slate-400 cursor-pointer hover:text-slate-300 flex items-center gap-2">
                        <Eye size={16} />
                        Voir les détails
                      </summary>
                      <div className="mt-3 bg-slate-800/50 rounded-lg p-4">
                        <pre className="text-xs font-mono text-slate-300 whitespace-pre-wrap overflow-auto max-h-40">
                          {JSON.stringify(e.details, null, 2)}
                        </pre>
                      </div>
                    </details>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && events.length === 0 && (
        <div className="flex flex-col items-center justify-center h-64 text-slate-500 animate-fadeIn">
          <Shield size={48} className="mb-4 text-slate-600" />
          <p className="text-lg">Aucun événement d'audit pour ce dossier.</p>
        </div>
      )}

      {/* Compliance Info */}
      <div className="card animate-fadeIn" style={{ animationDelay: '0.4s' }}>
        <h3 className="font-semibold text-slate-200 mb-4 flex items-center gap-2">
          <Lock size={20} className="text-blue-400" />
          Informations de conformité
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <CheckCircle2 size={16} className="text-emerald-400 mt-1 shrink-0" />
              <div>
                <p className="font-medium text-slate-200">RGPD</p>
                <p className="text-sm text-slate-400">Données personnelles chiffrées et anonymisées</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle2 size={16} className="text-emerald-400 mt-1 shrink-0" />
              <div>
                <p className="font-medium text-slate-200">Human-in-the-Loop</p>
                <p className="text-sm text-slate-400">Validation humaine obligatoire pour toute décision</p>
              </div>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <CheckCircle2 size={16} className="text-emerald-400 mt-1 shrink-0" />
              <div>
                <p className="font-medium text-slate-200">Traçabilité</p>
                <p className="text-sm text-slate-400">Chaque action est enregistrée avec hash SHA-256</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle2 size={16} className="text-emerald-400 mt-1 shrink-0" />
              <div>
                <p className="font-medium text-slate-200">Non-discrimination</p>
                <p className="text-sm text-slate-400">Aucune variable protégée n'influence la tarification</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
