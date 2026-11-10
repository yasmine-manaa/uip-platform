import { useEffect, useState } from 'react';
import { Database, BarChart3, TrendingUp, Users, PieChart, Activity, Loader2, MapPin, Car } from 'lucide-react';
import { api } from '../services/api';
import type { DatasetStats } from '../types';

export default function DatasetPage() {
  const [stats, setStats] = useState<DatasetStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getDatasetStats()
      .then(setStats)
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="text-slate-400 flex items-center gap-3">
          <Loader2 size={24} className="animate-spin" /> Chargement des données réelles…
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="text-red-400">{error || 'Données indisponibles'}</div>
      </div>
    );
  }

  const statCards = [
    { label: 'Polices', value: stats.total_policies.toLocaleString(), icon: <Users size={24} />, color: 'text-blue-400', gradient: 'from-blue-500/20 to-blue-600/10' },
    { label: 'Sinistres', value: stats.total_claims.toLocaleString(), icon: <BarChart3 size={24} />, color: 'text-emerald-400', gradient: 'from-emerald-500/20 to-emerald-600/10' },
    { label: 'Fréquence', value: `${(stats.claim_stats.claim_frequency * 100).toFixed(1)}%`, icon: <TrendingUp size={24} />, color: 'text-violet-400', gradient: 'from-violet-500/20 to-violet-600/10' },
    { label: 'Montant moyen', value: `${stats.avg_claim_amount.toFixed(0)}€`, icon: <Activity size={24} />, color: 'text-amber-400', gradient: 'from-amber-500/20 to-amber-600/10' },
  ];

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4 animate-fadeIn">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-600 flex items-center justify-center shadow-lg">
          <Database size={32} className="text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold gradient-text">Dataset Actuariel</h1>
          <p className="text-slate-400 mt-1">
            {stats.dataset_source} - {stats.total_records.toLocaleString()} enregistrements réels
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {statCards.map((card, i) => (
          <div key={i} className={`card card-hover bg-gradient-to-br ${card.gradient} animate-slideIn`} style={{ animationDelay: `${i * 0.1}s` }}>
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-xl bg-slate-800/50 ${card.color}`}>
                {card.icon}
              </div>
            </div>
            <p className="text-slate-400 text-sm mb-1">{card.label}</p>
            <p className={`text-3xl font-bold ${card.color}`}>{card.value}</p>
          </div>
        ))}
      </div>

      {/* Feature Statistics */}
      <div className="card animate-fadeIn" style={{ animationDelay: '0.4s' }}>
        <h2 className="text-xl font-semibold text-slate-200 mb-6 flex items-center gap-2">
          <BarChart3 size={20} className="text-blue-400" />
          Statistiques des variables prédictives
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Object.entries(stats.feature_stats).map(([key, value]) => (
            <div key={key} className="bg-slate-800/50 rounded-xl p-4">
              <h3 className="font-semibold text-slate-200 mb-3 capitalize">{key.replace(/_/g, ' ')}</h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-slate-400">Moyenne</p>
                  <p className="text-slate-200 font-mono">{value.mean.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-slate-400">Écart-type</p>
                  <p className="text-slate-200 font-mono">{value.std.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-slate-400">Min</p>
                  <p className="text-slate-200 font-mono">{value.min}</p>
                </div>
                <div>
                  <p className="text-slate-400">Max</p>
                  <p className="text-slate-200 font-mono">{value.max}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Claim Statistics */}
      <div className="card animate-fadeIn" style={{ animationDelay: '0.5s' }}>
        <h2 className="text-xl font-semibold text-slate-200 mb-6 flex items-center gap-2">
          <TrendingUp size={20} className="text-emerald-400" />
          Statistiques des sinistres
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
          <div className="text-center p-4 bg-slate-800/50 rounded-xl">
            <p className="text-2xl font-bold text-emerald-400">{stats.claim_stats.total_claims.toLocaleString()}</p>
            <p className="text-sm text-slate-400">Total sinistres</p>
          </div>
          <div className="text-center p-4 bg-slate-800/50 rounded-xl">
            <p className="text-2xl font-bold text-blue-400">{stats.claim_stats.avg_claims_per_policy.toFixed(3)}</p>
            <p className="text-sm text-slate-400">Moyenne par police</p>
          </div>
          <div className="text-center p-4 bg-slate-800/50 rounded-xl">
            <p className="text-2xl font-bold text-violet-400">{(stats.claim_stats.claim_frequency * 100).toFixed(1)}%</p>
            <p className="text-sm text-slate-400">Fréquence sinistre</p>
          </div>
          <div className="text-center p-4 bg-slate-800/50 rounded-xl">
            <p className="text-2xl font-bold text-amber-400">{stats.claim_stats.total_claim_amount.toLocaleString()}€</p>
            <p className="text-sm text-slate-400">Montant total</p>
          </div>
          <div className="text-center p-4 bg-slate-800/50 rounded-xl">
            <p className="text-2xl font-bold text-pink-400">{stats.claim_stats.avg_claim_amount.toFixed(0)}€</p>
            <p className="text-sm text-slate-400">Montant moyen</p>
          </div>
          <div className="text-center p-4 bg-slate-800/50 rounded-xl">
            <p className="text-2xl font-bold text-red-400">{stats.claim_stats.max_claim_amount.toLocaleString()}€</p>
            <p className="text-sm text-slate-400">Montant max</p>
          </div>
        </div>
      </div>

      {/* Top Regions and Brands */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Top Regions */}
        <div className="card animate-fadeIn" style={{ animationDelay: '0.6s' }}>
          <h2 className="text-xl font-semibold text-slate-200 mb-6 flex items-center gap-2">
            <MapPin size={20} className="text-blue-400" />
            Top 10 Régions
          </h2>
          <div className="space-y-3">
            {Object.entries(stats.top_regions).map(([region, count], i) => (
              <div key={region} className="flex items-center justify-between">
                <span className="text-sm text-slate-300">{region}</span>
                <div className="flex items-center gap-3">
                  <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
                      style={{ width: `${(count / stats.total_policies) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-mono text-slate-400 w-12">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Brands */}
        <div className="card animate-fadeIn" style={{ animationDelay: '0.7s' }}>
          <h2 className="text-xl font-semibold text-slate-200 mb-6 flex items-center gap-2">
            <Car size={20} className="text-emerald-400" />
            Top 10 Marques
          </h2>
          <div className="space-y-3">
            {Object.entries(stats.top_brands).map(([brand, count], i) => (
              <div key={brand} className="flex items-center justify-between">
                <span className="text-sm text-slate-300">{brand}</span>
                <div className="flex items-center gap-3">
                  <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full"
                      style={{ width: `${(count / stats.total_policies) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-mono text-slate-400 w-12">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
