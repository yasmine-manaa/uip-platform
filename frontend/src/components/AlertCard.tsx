import { AlertTriangle, Info, XCircle } from 'lucide-react';
import type { AgentAlert } from '../types';

const config = {
  CRITICAL: {
    border: 'border-red-700/50',
    bg: 'bg-red-950/50',
    text: 'text-red-300',
    icon: <XCircle size={20} className="text-red-400 shrink-0" />,
  },
  WARNING: {
    border: 'border-amber-700/50',
    bg: 'bg-amber-950/50',
    text: 'text-amber-300',
    icon: <AlertTriangle size={20} className="text-amber-400 shrink-0" />,
  },
  INFO: {
    border: 'border-blue-700/50',
    bg: 'bg-blue-950/50',
    text: 'text-blue-300',
    icon: <Info size={20} className="text-blue-400 shrink-0" />,
  },
};

interface AlertCardProps {
  alert: AgentAlert;
}

export default function AlertCard({ alert }: AlertCardProps) {
  const c = config[alert.severity] ?? config.INFO;
  return (
    <div className={`flex items-start gap-3 p-4 rounded-xl border ${c.border} ${c.bg}`}>
      {c.icon}
      <div className="flex-1">
        <span className={`text-xs font-semibold uppercase tracking-wide ${c.text}`}>
          {alert.code}
        </span>
        <p className={`text-sm mt-1 ${c.text}`}>{alert.message}</p>
        {alert.action_required && (
          <p className="text-xs text-slate-400 mt-2 flex items-start gap-1">
            <span className="text-slate-500">Action:</span> {alert.action_required}
          </p>
        )}
      </div>
    </div>
  );
}
