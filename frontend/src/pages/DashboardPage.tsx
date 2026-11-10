import { useEffect, useState } from 'react';
import { Plus, RefreshCw, Users, FileText, BarChart3, Shield, Loader2 } from 'lucide-react';
import { api } from '../services/api';
import type { Case } from '../types';
import StatusBadge from '../components/StatusBadge';
import type { Page } from '../components/Sidebar';

interface DashboardPageProps {
  onNavigate: (page: Page, caseId?: string) => void;
}

export default function DashboardPage({ onNavigate }: DashboardPageProps) {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listCases();
      setCases(data);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between animate-fadeIn">
        <div>
          <h1 className="text-3xl font-bold gradient-text">Tableau de bord</h1>
          <p className="text-slate-400 mt-2">
            {cases.length} dossier(s) en portefeuille
          </p>
        </div>
        <div className="flex gap-3">
          <button onClick={load} className="btn-secondary flex items-center gap-2">
            <RefreshCw size={16} /> Actualiser
          </button>
          <button
            onClick={() => onNavigate('new-case')}
            className="btn-primary flex items-center gap-2"
          >
            <Plus size={16} /> Nouveau dossier
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {[
          { label: 'Total dossiers', value: cases.length, color: 'text-blue-400', icon: <Users size={24} />, gradient: 'from-blue-500/20 to-blue-600/10' },
          { label: 'En analyse', value: cases.filter(c => c.status === 'ANALYZED').length, color: 'text-amber-400', icon: <BarChart3 size={24} />, gradient: 'from-amber-500/20 to-amber-600/10' },
          { label: 'Revue requise', value: cases.filter(c => c.status === 'UNDER_REVIEW').length, color: 'text-violet-400', icon: <Shield size={24} />, gradient: 'from-violet-500/20 to-violet-600/10' },
          { label: 'Approuvés', value: cases.filter(c => c.status === 'APPROVED').length, color: 'text-emerald-400', icon: <FileText size={24} />, gradient: 'from-emerald-500/20 to-emerald-600/10' },
        ].map((kpi, i) => (
          <div key={kpi.label} className={`card card-hover bg-gradient-to-br ${kpi.gradient} animate-slideIn`} style={{ animationDelay: `${i * 0.1}s` }}>
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-xl bg-slate-800/50 ${kpi.color}`}>
                {kpi.icon}
              </div>
            </div>
            <p className="text-slate-400 text-sm mb-1">{kpi.label}</p>
            <p className={`text-4xl font-bold ${kpi.color}`}>{kpi.value}</p>
          </div>
        ))}
      </div>

      {/* Case table */}
      <div className="card overflow-hidden animate-fadeIn" style={{ animationDelay: '0.4s' }}>
        <div className="px-6 py-4 border-b border-slate-700/50 flex items-center gap-3">
          <Users size={20} className="text-blue-400" />
          <span className="font-semibold text-slate-200 text-lg">Dossiers récents</span>
        </div>
        {loading ? (
          <div className="flex items-center justify-center h-48 text-slate-400">
            <Loader2 size={24} className="animate-spin mr-2" /> Chargement…
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-48 text-red-400">{error}</div>
        ) : cases.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-slate-500">
            <Users size={48} className="mb-4 text-slate-600" />
            <p className="text-lg">Aucun dossier — créez-en un avec le bouton ci-dessus</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50 bg-slate-800/30">
                  {['Référence', 'Assuré', 'Statut', 'Risque', 'Décision', 'Créé le'].map(h => (
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
                    onClick={() => onNavigate('decision', c.id)}
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
                    <td className="px-6 py-4 text-slate-400 text-xs">
                      {new Date(c.created_at).toLocaleDateString('fr-FR')}
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
