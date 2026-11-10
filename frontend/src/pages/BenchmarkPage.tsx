import { useEffect, useState } from 'react';
import { Loader2, FlaskConical, TrendingUp, Award, BarChart3 } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer,
} from 'recharts';
import { api } from '../services/api';
import type { ScientificValidation, BenchmarkResult } from '../types';

const COLORS = ['#60a5fa', '#34d399', '#f59e0b', '#a78bfa'];

function MetricBar({ results, metric, label }: {
  results: BenchmarkResult[];
  metric: keyof BenchmarkResult['metrics'];
  label: string;
}) {
  const data = results.map((r, i) => ({
    name: r.config.name.replace('Configuration ', 'Cfg '),
    value: parseFloat((r.metrics[metric] as number * 100).toFixed(1)),
    fill: COLORS[i],
  }));

  return (
    <div className="card">
      <p className="text-sm font-semibold text-slate-300 mb-4">{label}</p>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} barSize={32}>
          <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
          <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} domain={[0, 100]} unit="%" />
          <Tooltip
            contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
            labelStyle={{ color: '#e2e8f0' }}
            formatter={(v: number) => [`${v}%`, label]}
          />
          {data.map((d, i) => (
            <Bar key={i} dataKey="value" data={[d]} fill={d.fill} radius={[4, 4, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function RadarComparison({ results }: { results: BenchmarkResult[] }) {
  const radarData = [
    { metric: 'Accuracy' },
    { metric: 'Precision' },
    { metric: 'Recall' },
    { metric: 'F1' },
    { metric: 'Citations' },
    { metric: 'Explicabilité' },
  ].map(row => {
    const metricMap: Record<string, keyof typeof results[0]['metrics']> = {
      Accuracy: 'accuracy',
      Precision: 'precision',
      Recall: 'recall',
      F1: 'f1_score',
      Citations: 'citation_coverage',
      Explicabilité: 'explainability_score',
    };
    const key = metricMap[row.metric];
    const enriched: Record<string, number | string> = { metric: row.metric };
    results.forEach((r, i) => {
      enriched[`Cfg ${i + 1}`] = parseFloat(((r.metrics[key] ?? 0) * 100).toFixed(1));
    });
    return enriched;
  });

  return (
    <div className="card">
      <p className="text-sm font-semibold text-slate-300 mb-4">Vue multi-dimensionnelle</p>
      <ResponsiveContainer width="100%" height={280}>
        <RadarChart data={radarData}>
          <PolarGrid stroke="#334155" />
          <PolarAngleAxis dataKey="metric" tick={{ fill: '#94a3b8', fontSize: 11 }} />
          {results.map((r, i) => (
            <Radar
              key={i}
              name={r.config.name.replace('Configuration ', 'Cfg ')}
              dataKey={`Cfg ${i + 1}`}
              stroke={COLORS[i]}
              fill={COLORS[i]}
              fillOpacity={0.15}
            />
          ))}
          <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 12 }} />
          <Tooltip
            contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function BenchmarkPage() {
  const [data, setData] = useState<ScientificValidation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getScientificValidation()
      .then(setData)
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-full gap-3 text-slate-400">
        <Loader2 size={24} className="animate-spin" /> Calcul du benchmark scientifique…
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 flex items-center justify-center h-full text-red-400">
        {error ?? 'Données indisponibles'}
      </div>
    );
  }

  const { results } = data;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4 animate-fadeIn">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-600 to-emerald-700 flex items-center justify-center shadow-lg">
          <FlaskConical size={32} className="text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold gradient-text">Benchmark Scientifique</h1>
          <p className="text-slate-400 mt-1">
            Comparaison de {results.length} configurations actuarielles — validation sur {results[0]?.sample_size ?? '?'} dossiers
          </p>
        </div>
      </div>

      {/* Config cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {results.map((r, i) => (
          <div key={i} className={`card card-hover animate-slideIn bg-gradient-to-br ${r.config.config_id === data.recommended_config ? 'from-blue-900/30 to-blue-800/20 border-blue-700/50' : 'from-slate-800/30 to-slate-700/20'}`} style={{ animationDelay: `${i * 0.1}s` }}>
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`p-3 rounded-xl ${r.config.config_id === data.recommended_config ? 'bg-blue-600' : 'bg-slate-700'}`}>
                  <BarChart3 size={20} className="text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-200 text-lg">{r.config.name}</h3>
                  <p className="text-xs text-slate-400 mt-1">{r.config.description}</p>
                </div>
              </div>
              {r.config.config_id === data.recommended_config && (
                <span className="px-3 py-1 bg-blue-900/50 text-blue-300 text-xs rounded-full border border-blue-700/50 flex items-center gap-1">
                  <Award size={12} /> Recommandé
                </span>
              )}
            </div>
            <div className="grid grid-cols-3 gap-4 mt-4">
              {[
                ['F1', (r.metrics.f1_score * 100).toFixed(0) + '%'],
                ['Precision', (r.metrics.precision * 100).toFixed(0) + '%'],
                ['Citations', (r.metrics.citation_coverage * 100).toFixed(0) + '%'],
              ].map(([k, v]) => (
                <div key={k} className="text-center p-3 bg-slate-800/50 rounded-lg">
                  <p className="text-xs text-slate-400 mb-1">{k}</p>
                  <p className="text-xl font-bold" style={{ color: COLORS[i] }}>{v}</p>
                </div>
              ))}
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {r.config.glm_frequency && <span className="text-xs bg-slate-700/50 text-slate-300 px-3 py-1 rounded-full border border-slate-600/50">GLM Freq</span>}
              {r.config.glm_severity && <span className="text-xs bg-slate-700/50 text-slate-300 px-3 py-1 rounded-full border border-slate-600/50">GLM Sév</span>}
              {r.config.ml_boost && <span className="text-xs bg-slate-700/50 text-slate-300 px-3 py-1 rounded-full border border-slate-600/50">XGBoost</span>}
              {r.config.rag_citations && <span className="text-xs bg-slate-700/50 text-slate-300 px-3 py-1 rounded-full border border-slate-600/50">RAG</span>}
              {r.config.multi_agent && <span className="text-xs bg-slate-700/50 text-slate-300 px-3 py-1 rounded-full border border-slate-600/50">Multi-Agent</span>}
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <MetricBar results={results} metric="f1_score" label="F1 Score (%)" />
        <MetricBar results={results} metric="citation_coverage" label="Couverture Citations (%)" />
        <MetricBar results={results} metric="explainability_score" label="Score Explicabilité (%)" />
        <MetricBar results={results} metric="precision" label="Précision (%)" />
      </div>

      <RadarComparison results={results} />

      {/* Metrics table */}
      <div className="card overflow-hidden animate-fadeIn">
        <div className="px-6 py-4 border-b border-slate-700/50 font-semibold text-slate-200 text-lg">
          Tableau comparatif complet
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700/50 bg-slate-800/30">
                <th className="table-header text-left px-6 py-4">Métrique</th>
                {results.map(r => (
                  <th key={r.config.config_id} className="table-header text-center px-6 py-4">
                    {r.config.name.replace('Configuration ', 'Cfg ')}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {([
                ['Accuracy', 'accuracy'],
                ['Precision', 'precision'],
                ['Recall', 'recall'],
                ['F1 Score', 'f1_score'],
                ['Couverture Citations', 'citation_coverage'],
                ['Explicabilité', 'explainability_score'],
                ['Temps (ms)', 'processing_time_ms'],
              ] as [string, keyof BenchmarkResult['metrics']][]).map(([label, key]) => (
                <tr key={key} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                  <td className="px-6 py-3 text-slate-300">{label}</td>
                  {results.map((r, i) => {
                    const val = r.metrics[key];
                    const formatted = key === 'processing_time_ms'
                      ? String(val)
                      : `${((val as number) * 100).toFixed(1)}%`;
                    return (
                      <td key={i} className="px-6 py-3 text-center font-mono"
                        style={{ color: COLORS[i] }}>{formatted}</td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Conclusion */}
      {data.conclusion && (
        <div className="card border border-blue-700/50 bg-gradient-to-br from-blue-900/30 to-cyan-900/30 animate-fadeIn">
          <h3 className="text-lg font-semibold text-blue-400 mb-3 flex items-center gap-2">
            <TrendingUp size={20} />
            Conclusion scientifique
          </h3>
          <p className="text-slate-300 leading-relaxed">{data.conclusion}</p>
        </div>
      )}
    </div>
  );
}
