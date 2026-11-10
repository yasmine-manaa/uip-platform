import type { RiskTier } from '../types';

const tiers: { key: RiskTier; label: string; color: string; gradient: string }[] = [
  { key: 'LOW',      label: 'Faible',   color: '#10b981', gradient: 'from-emerald-500 to-emerald-600' },
  { key: 'MODERATE', label: 'Modéré',   color: '#f59e0b', gradient: 'from-amber-500 to-amber-600' },
  { key: 'HIGH',     label: 'Haut',     color: '#ef4444', gradient: 'from-red-500 to-red-600' },
  { key: 'CRITICAL', label: 'Critique', color: '#b91c1c', gradient: 'from-red-700 to-red-800' },
];

interface RiskGaugeProps {
  tier: RiskTier;
  score?: number; // 0-1
}

export default function RiskGauge({ tier, score }: RiskGaugeProps) {
  const idx = tiers.findIndex(t => t.key === tier);
  const current = tiers[idx];
  const pct = score !== undefined ? score : (idx + 1) / tiers.length;

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <span className="text-sm font-medium text-slate-300">Niveau de risque</span>
        {score !== undefined && (
          <span className="text-sm font-mono text-slate-400">{(pct * 100).toFixed(0)}%</span>
        )}
      </div>
      {/* Bar track */}
      <div className="relative h-4 rounded-full bg-slate-800 overflow-hidden">
        <div
          className={`absolute left-0 top-0 h-full rounded-full bg-gradient-to-r ${current?.gradient || 'from-slate-500 to-slate-600'} transition-all duration-500`}
          style={{ width: `${pct * 100}%` }}
        />
      </div>
      {/* Tier labels */}
      <div className="flex justify-between">
        {tiers.map((t, i) => (
          <span
            key={t.key}
            className={`text-xs font-medium ${i === idx ? 'text-slate-200' : 'text-slate-600'}`}
            style={i === idx ? { color: current?.color } : {}}
          >
            {t.label}
          </span>
        ))}
      </div>
    </div>
  );
}
