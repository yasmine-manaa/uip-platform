import { useEffect, useState, useCallback } from 'react';
import {
  CheckCircle2, AlertTriangle, XCircle, Loader2,
  RefreshCw, ChevronRight, ThumbsUp, ThumbsDown, Brain,
  FileText, Users, Shield, BarChart3
} from 'lucide-react';
import { api } from '../services/api';
import type { Case, Decision, AgentOutput, HumanReviewCreate, AnalysisFindings } from '../types';
import AgentCard from '../components/AgentCard';
import RiskGauge from '../components/RiskGauge';
import StatusBadge from '../components/StatusBadge';

interface DecisionPageProps {
  activeCaseId: string | null;
  setActiveCaseId?: (id: string) => void;
}

const decisionLabel: Record<string, string> = {
  PROCEED_STANDARD:        'Émettre la police standard',
  SPECIAL_TERMS_OFFER:     'Proposition avec conditions particulières',
  REQUEST_ADDITIONAL_INFO: 'Demander informations complémentaires',
  REQUIRE_SENIOR_REVIEW:   'Référer au souscripteur senior',
  ANALYSIS_IMPOSSIBLE:     'Analyse impossible',
};

const decisionColor: Record<string, string> = {
  PROCEED_STANDARD:        'from-emerald-600 to-emerald-700',
  SPECIAL_TERMS_OFFER:     'from-amber-600 to-amber-700',
  REQUEST_ADDITIONAL_INFO: 'from-blue-600 to-blue-700',
  REQUIRE_SENIOR_REVIEW:   'from-violet-600 to-violet-700',
  ANALYSIS_IMPOSSIBLE:     'from-red-600 to-red-700',
};

export default function DecisionPage({ activeCaseId, setActiveCaseId }: DecisionPageProps) {
  const [caseData, setCaseData] = useState<Case | null>(null);
  const [decision, setDecision] = useState<Decision | null>(null);
  const [agents, setAgents] = useState<AgentOutput[]>([]);
  const [findings, setFindings] = useState<AnalysisFindings | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableCases, setAvailableCases] = useState<Case[]>([]);

  // Human review form
  const [reviewForm, setReviewForm] = useState<HumanReviewCreate>({
    underwriter_name: '',
    underwriter_role: 'Souscripteur',
    decision: 'ACCEPTED',
    justification: '',
  });
  const [reviewStatus, setReviewStatus] = useState<'idle' | 'submitting' | 'done' | 'error'>('idle');

  const load = useCallback(async () => {
    if (!activeCaseId) return;
    setLoading(true);
    setError(null);
    try {
      const [c, findingsData] = await Promise.all([
        api.getCase(activeCaseId),
        api.getFindings(activeCaseId).catch(() => null),
      ]);
      setCaseData(c);
      setFindings(findingsData);
      
      if (findingsData) {
        // Convert agent_outputs object to array
        const agentArray = Object.values(findingsData.agent_outputs || {}) as AgentOutput[];
        setAgents(agentArray);
        setDecision(findingsData.provisional_decision || null);
      }
      
      // Fallback to decision endpoint if no findings
      if (!findingsData?.provisional_decision) {
        const dec = await api.getDecision(activeCaseId).catch(() => null);
        if (dec) setDecision(dec);
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [activeCaseId]);

  const loadAvailableCases = useCallback(async () => {
    try {
      const cases = await api.listCases();
      setAvailableCases(cases);
    } catch (e) {
      console.error('Failed to load cases:', e);
    }
  }, []);

  useEffect(() => {
    load();
    loadAvailableCases();
  }, [load, loadAvailableCases]);

  const submitReview = async () => {
    if (!activeCaseId) return;
    setReviewStatus('submitting');
    try {
      await api.submitReview(activeCaseId, reviewForm);
      setReviewStatus('done');
    } catch (e) {
      setError(String(e));
      setReviewStatus('error');
    }
  };

  if (!activeCaseId) {
    return (
      <div className="p-8 flex flex-col items-center justify-center h-full gap-6 animate-fadeIn">
        <div className="w-20 h-20 rounded-2xl bg-slate-800 flex items-center justify-center">
          <Brain size={40} className="text-slate-500" />
        </div>
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold text-slate-100">Dossier — Décision</h2>
          <p className="text-slate-400">
            Sélectionnez un dossier pour voir la décision algorithmique et les résultats des agents.
          </p>
        </div>
        <div className="card w-full max-w-4xl">
          <div className="px-6 py-4 border-b border-slate-700/50">
            <p className="font-semibold text-slate-200 text-lg">Dossiers disponibles</p>
          </div>
          {availableCases.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-slate-500">
              <FileText size={48} className="mb-4 text-slate-600" />
              <p>Aucun dossier disponible</p>
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
                  {availableCases.map(c => (
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

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-full gap-3 text-slate-400">
        <Loader2 size={24} className="animate-spin" /> Chargement…
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between animate-fadeIn">
        <div>
          <h1 className="text-3xl font-bold gradient-text">Dossier — Décision</h1>
          {caseData && (
            <p className="text-slate-400 mt-2">
              {caseData.reference} · {caseData.applicant_name}
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          {caseData && <StatusBadge value={caseData.status} />}
          <button onClick={load} className="btn-secondary flex items-center gap-2">
            <RefreshCw size={16} /> Actualiser
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-950/50 border border-red-700/50 rounded-xl text-red-300 flex items-center gap-3">
          <AlertTriangle size={20} /> {error}
        </div>
      )}

      {/* Decision Card */}
      {decision && (
        <div className={`card animate-slideIn bg-gradient-to-br ${decisionColor[decision.decision_code] || 'from-slate-600 to-slate-700'} border-white/10`}>
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className="p-4 rounded-xl bg-white/10 backdrop-blur-sm">
                <Brain size={32} className="text-white" />
              </div>
              <div>
                <p className="text-sm text-white/70 uppercase tracking-wide mb-1">Décision algorithmique</p>
                <h2 className="text-2xl font-bold text-white">
                  {decisionLabel[decision.decision_code] ?? decision.decision_title ?? decision.decision_code}
                </h2>
                <p className="text-sm text-white/80 mt-1">
                  Confiance {(decision.confidence_level * 100).toFixed(0)}% ·{' '}
                  {decision.risk_tier && <StatusBadge value={decision.risk_tier} className="ml-2" />}
                </p>
              </div>
            </div>
            <div className="text-right">
              {decision.pure_premium_estimate !== undefined && (
                <div>
                  <p className="text-sm text-white/70">Prime pure estimée</p>
                  <p className="text-3xl font-mono font-bold text-white">
                    {decision.pure_premium_estimate.toFixed(0)} €/an
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Justification */}
          {decision.justification && (
            <p className="text-white/90 italic border-t border-white/20 pt-4 mt-4">
              {decision.justification}
            </p>
          )}

          {/* Risk gauge */}
          {decision.risk_tier && (
            <div className="mt-6">
              <RiskGauge tier={decision.risk_tier} />
            </div>
          )}

          {/* Factors */}
          <div className="grid grid-cols-2 gap-6 mt-6">
            {decision.favorable_factors?.length > 0 && (
              <div className="bg-white/10 rounded-xl p-4">
                <p className="flex items-center gap-2 text-sm font-semibold text-emerald-300 mb-3">
                  <ThumbsUp size={16} /> Facteurs favorables
                </p>
                <ul className="space-y-2">
                  {decision.favorable_factors.map((f, i) => (
                    <li key={i} className="text-sm text-white/80 flex items-start gap-2">
                      <CheckCircle2 size={14} className="mt-0.5 shrink-0 text-emerald-400" /> {f}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {decision.unfavorable_factors?.length > 0 && (
              <div className="bg-white/10 rounded-xl p-4">
                <p className="flex items-center gap-2 text-sm font-semibold text-red-300 mb-3">
                  <ThumbsDown size={16} /> Facteurs défavorables
                </p>
                <ul className="space-y-2">
                  {decision.unfavorable_factors.map((f, i) => (
                    <li key={i} className="text-sm text-white/80 flex items-start gap-2">
                      <XCircle size={14} className="mt-0.5 shrink-0 text-red-400" /> {f}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Required actions */}
          {decision.required_actions?.length > 0 && (
            <div className="mt-6 bg-white/10 rounded-xl p-4">
              <p className="text-sm font-semibold uppercase tracking-wide text-white/80 mb-3">
                Actions requises
              </p>
              <ul className="space-y-2">
                {decision.required_actions.map((a, i) => (
                  <li key={i} className="text-sm text-white/90 flex items-start gap-3">
                    <span className="shrink-0 font-bold bg-white/20 px-2 py-1 rounded">{i + 1}</span>
                    {a}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Contradictions & Timeline */}
      {findings && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {findings.contradictions?.length > 0 && (
            <div className="card border border-red-600/50 animate-slideIn">
              <h3 className="font-semibold text-red-400 mb-4 flex items-center gap-2">
                <AlertTriangle size={20} /> Contradictions détectées
              </h3>
              <ul className="space-y-2">
                {findings.contradictions.map((c, i) => (
                  <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                    <span className="text-red-400">•</span> {c}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {findings.execution_timeline?.length > 0 && (
            <div className="card animate-slideIn">
              <h3 className="font-semibold text-slate-200 mb-4 flex items-center gap-2">
                <BarChart3 size={20} className="text-blue-400" /> Timeline d'exécution
              </h3>
              <div className="space-y-3">
                {findings.execution_timeline.map((step, i) => (
                  <div key={i} className="flex items-start gap-3 text-sm">
                    <div className="w-3 h-3 rounded-full bg-blue-400 mt-1.5 shrink-0" />
                    <div>
                      <p className="font-medium text-slate-200">{step.step}</p>
                      <p className="text-slate-400 text-xs">{step.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Agent Outputs */}
      {agents.length > 0 && (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3 animate-fadeIn">
            <Users size={24} className="text-blue-400" />
            Résultats des agents ({agents.length})
          </h2>
          {agents.map((a, i) => (
            <AgentCard key={a.agent_id} agent={a} defaultOpen={i === 0} />
          ))}
        </div>
      )}

      {/* Human Review */}
      <div className="card animate-fadeIn">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600">
            <Shield size={24} className="text-white" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-slate-200">Validation souscripteur</h2>
            <p className="text-sm text-slate-400">Human-in-the-Loop — Validation humaine obligatoire</p>
          </div>
        </div>

        {reviewStatus === 'done' ? (
          <div className="flex items-center gap-3 p-4 bg-emerald-900/50 border border-emerald-700/50 rounded-xl text-emerald-300">
            <CheckCircle2 size={20} /> Revue soumise avec succès.
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Nom du souscripteur</label>
                <input className="input-field" value={reviewForm.underwriter_name}
                  onChange={e => setReviewForm(f => ({ ...f, underwriter_name: e.target.value }))} />
              </div>
              <div>
                <label className="label">Rôle</label>
                <select className="input-field" value={reviewForm.underwriter_role}
                  onChange={e => setReviewForm(f => ({ ...f, underwriter_role: e.target.value }))}>
                  {['Souscripteur', 'Souscripteur Senior', 'Responsable Souscription', 'Actuaire'].map(r => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="label">Décision</label>
              <select className="input-field" value={reviewForm.decision}
                onChange={e => setReviewForm(f => ({ ...f, decision: e.target.value }))}>
                {['ACCEPTED', 'MODIFIED', 'INFO_REQUESTED', 'ESCALATED_SENIOR', 'REFUSED'].map(d => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Prime finale (EUR/an)</label>
                <input type="number" className="input-field" value={reviewForm.final_premium_eur || ''}
                  onChange={e => setReviewForm(f => ({ ...f, final_premium_eur: parseFloat(e.target.value) || undefined }))} />
              </div>
              <div>
                <label className="label">Chargement technique (%)</label>
                <input type="number" className="input-field" value={reviewForm.technical_loading_pct || ''}
                  onChange={e => setReviewForm(f => ({ ...f, technical_loading_pct: parseFloat(e.target.value) || undefined }))} />
              </div>
            </div>
            <div>
              <label className="label">Justification / Motivation</label>
              <textarea
                className="input-field min-h-[120px] resize-none"
                value={reviewForm.justification}
                onChange={e => setReviewForm(f => ({ ...f, justification: e.target.value }))}
                placeholder="Justification détaillée de la décision…"
              />
            </div>
            <button
              onClick={submitReview}
              disabled={reviewStatus === 'submitting' || !reviewForm.underwriter_name || !reviewForm.justification}
              className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {reviewStatus === 'submitting'
                ? <><Loader2 size={20} className="animate-spin" /> Envoi…</>
                : <><CheckCircle2 size={20} /> Valider la revue</>}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
