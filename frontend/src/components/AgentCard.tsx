import { useState } from 'react';
import { ChevronDown, ChevronRight, CheckCircle, AlertTriangle, XCircle, Clock, Brain } from 'lucide-react';
import type { AgentOutput } from '../types';
import AlertCard from './AlertCard';
import CitationCard from './CitationCard';

const agentColors: Record<string, string> = {
  'AGENT_01_CUSTOMER_PROFILE':    'from-blue-500 to-blue-600',
  'AGENT_02_POLICY_DOCUMENT':     'from-violet-500 to-violet-600',
  'AGENT_03_RISK_ASSESSMENT':      'from-orange-500 to-orange-600',
  'AGENT_04_HISTORICAL_CLAIMS':    'from-red-500 to-red-600',
  'AGENT_05_EXTERNAL_INTELLIGENCE': 'from-cyan-500 to-cyan-600',
  'AGENT_06_GOVERNANCE_TRUST':     'from-emerald-500 to-emerald-600',
};

const StatusIcon = ({ status }: { status: string }) => {
  if (status === 'SUCCESS') return <CheckCircle size={20} className="text-emerald-400" />;
  if (status === 'WARNING') return <AlertTriangle size={20} className="text-amber-400" />;
  if (status === 'DATA_DEFICIENT') return <Clock size={20} className="text-blue-400" />;
  return <XCircle size={20} className="text-red-400" />;
};

interface AgentCardProps {
  agent: AgentOutput;
  defaultOpen?: boolean;
}

export default function AgentCard({ agent, defaultOpen = false }: AgentCardProps) {
  const [open, setOpen] = useState(defaultOpen);
  const gradient = agentColors[agent.agent_id] || 'from-slate-500 to-slate-600';

  return (
    <div className="card card-hover overflow-hidden animate-slideIn">
      {/* Header */}
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between p-6 text-left hover:bg-slate-800/30 transition-colors"
      >
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-xl bg-gradient-to-br ${gradient}`}>
            <Brain size={24} className="text-white" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <StatusIcon status={agent.status} />
              <p className="font-semibold text-slate-100 text-lg">{agent.agent_name}</p>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              v{agent.version} · Confiance {(agent.confidence_score * 100).toFixed(0)}% ·{' '}
              {agent.alerts?.length || 0} alerte(s) · {agent.sources?.length || 0} citation(s)
            </p>
          </div>
        </div>
        {open ? <ChevronDown size={20} className="text-slate-400" /> : <ChevronRight size={20} className="text-slate-400" />}
      </button>

      {/* Body */}
      {open && (
        <div className="p-6 border-t border-slate-700/30 space-y-6">
          {/* Findings */}
          {agent.findings && agent.findings.length > 0 && (
            <div>
              <p className="text-sm text-slate-400 uppercase tracking-wide mb-3 font-semibold">Résultats</p>
              <div className="bg-slate-800/50 rounded-xl p-4 space-y-2">
                {agent.findings.map((finding, i) => (
                  <p key={i} className="text-sm text-slate-300 flex items-start gap-2">
                    <span className="text-blue-400 mt-1">•</span>
                    {finding}
                  </p>
                ))}
              </div>
            </div>
          )}

          {/* Alerts */}
          {agent.alerts && agent.alerts.length > 0 && (
            <div>
              <p className="text-sm text-slate-400 uppercase tracking-wide mb-3 font-semibold">Alertes</p>
              <div className="space-y-2">
                {agent.alerts.map((a, i) => <AlertCard key={i} alert={a} />)}
              </div>
            </div>
          )}

          {/* Evidence */}
          {agent.evidence && agent.evidence.length > 0 && (
            <div>
              <p className="text-sm text-slate-400 uppercase tracking-wide mb-3 font-semibold">Preuves</p>
              <div className="bg-slate-800/50 rounded-xl p-4 space-y-2">
                {agent.evidence.map((e, i) => (
                  <div key={i} className="text-sm text-slate-300 flex items-start gap-2">
                    <span className="font-medium text-blue-400">{e.key}:</span>
                    <span>{String(e.value)}</span>
                    {e.source_ref && <span className="text-slate-500">({e.source_ref})</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sources / Citations */}
          {agent.sources && agent.sources.length > 0 && (
            <div>
              <p className="text-sm text-slate-400 uppercase tracking-wide mb-3 font-semibold">Citations réglementaires</p>
              <div className="space-y-2">
                {agent.sources.map((s, i) => <CitationCard key={i} citation={s} index={i} />)}
              </div>
            </div>
          )}

          {/* Missing fields */}
          {agent.missing_fields && agent.missing_fields.length > 0 && (
            <div>
              <p className="text-sm text-slate-400 uppercase tracking-wide mb-3 font-semibold">Champs manquants</p>
              <div className="bg-slate-800/50 rounded-xl p-4">
                <div className="flex flex-wrap gap-2">
                  {agent.missing_fields.map((field, i) => (
                    <span key={i} className="text-xs bg-red-900/50 text-red-200 px-3 py-1 rounded-full border border-red-700/50">
                      {field}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Timestamp */}
          {agent.timestamp && (
            <p className="text-xs text-slate-500">
              Exécuté le {new Date(agent.timestamp).toLocaleString('fr-FR')}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
