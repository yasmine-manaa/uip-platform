import type { CaseStatus, RiskTier, AlertSeverity } from '../types';

type Variant = CaseStatus | RiskTier | AlertSeverity | string;

const palette: Record<string, string> = {
  // Case status
  DRAFT: 'bg-slate-700/50 text-slate-200 border-slate-600/50',
  ANALYZED: 'bg-blue-900/50 text-blue-300 border-blue-700/50',
  UNDER_REVIEW: 'bg-amber-900/50 text-amber-300 border-amber-700/50',
  APPROVED: 'bg-emerald-900/50 text-emerald-300 border-emerald-700/50',
  MODIFIED: 'bg-yellow-900/50 text-yellow-300 border-yellow-700/50',
  ESCALATED: 'bg-violet-900/50 text-violet-300 border-violet-700/50',
  CLOSED: 'bg-slate-800/50 text-slate-400 border-slate-700/50',

  // Risk tier
  LOW: 'bg-emerald-900/50 text-emerald-300 border-emerald-700/50',
  MODERATE: 'bg-yellow-900/50 text-yellow-300 border-yellow-700/50',
  HIGH: 'bg-red-900/50 text-red-300 border-red-700/50',
  CRITICAL: 'bg-red-950/50 text-red-400 border-red-800/50 font-bold',

  // Alert severity
  INFO: 'bg-blue-900/50 text-blue-300 border-blue-700/50',
  WARNING: 'bg-amber-900/50 text-amber-300 border-amber-700/50',

  // Agent status
  SUCCESS: 'bg-emerald-900/50 text-emerald-300 border-emerald-700/50',
  DATA_DEFICIENT: 'bg-blue-900/50 text-blue-300 border-blue-700/50',
};

const labels: Record<string, string> = {
  DRAFT: 'Brouillon',
  ANALYZED: 'Analysé',
  UNDER_REVIEW: 'En revue',
  APPROVED: 'Approuvé',
  MODIFIED: 'Modifié',
  ESCALATED: 'Escaladé',
  CLOSED: 'Clôturé',
  LOW: 'Faible',
  MODERATE: 'Modéré',
  HIGH: 'Haut',
  CRITICAL: 'Critique',
  INFO: 'Info',
  WARNING: 'Alerte',
  SUCCESS: 'Succès',
  DATA_DEFICIENT: 'Données insuffisantes',
};

interface StatusBadgeProps {
  value: Variant;
  className?: string;
}

export default function StatusBadge({ value, className = '' }: StatusBadgeProps) {
  const color = palette[value] ?? 'bg-slate-700/50 text-slate-300 border-slate-600/50';
  const label = labels[value] ?? value;
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${color} ${className}`}>
      {label}
    </span>
  );
}
