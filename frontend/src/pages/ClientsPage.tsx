import { useEffect, useState } from 'react';
import { Users, Plus, RefreshCw, UserPlus, History } from 'lucide-react';
import { api } from '../services/api';
import type { Client } from '../types';

interface ClientsPageProps {
  onNavigate: (page: string, caseId?: string, clientId?: string) => void;
}

export default function ClientsPage({ onNavigate }: ClientsPageProps) {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listClients();
      setClients(data);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between animate-fadeIn">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-600 flex items-center justify-center shadow-lg">
            <Users size={32} className="text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold gradient-text">Clients</h1>
            <p className="text-slate-400 mt-1">
              Gestion des clients récurrents et historique
            </p>
          </div>
        </div>
        <div className="flex gap-3">
          <button onClick={load} className="btn-secondary flex items-center gap-2">
            <RefreshCw size={16} /> Actualiser
          </button>
          <button className="btn-primary flex items-center gap-2">
            <Plus size={16} /> Nouveau client
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-950/50 border border-red-700/50 rounded-xl text-red-300">
          {error}
        </div>
      )}

      {/* Clients Grid */}
      {clients.length === 0 ? (
        <div className="card card-hover animate-fadeIn">
          <div className="flex flex-col items-center justify-center py-12">
            <Users size={64} className="text-slate-600 mb-4" />
            <h3 className="text-xl font-semibold text-slate-200 mb-2">Aucun client</h3>
            <p className="text-slate-400 text-center max-w-md">
              Créez votre premier client pour commencer à gérer les dossiers récurrents.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {clients.map((client, i) => (
            <div key={client.id} className="card card-hover animate-slideIn" style={{ animationDelay: `${i * 0.1}s` }}>
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600">
                    <UserPlus size={20} className="text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-200">{client.full_name}</h3>
                    <p className="text-xs text-slate-400">{client.client_reference}</p>
                  </div>
                </div>
              </div>
              
              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Âge:</span>
                  <span className="text-slate-200">{client.driver_age || 'N/A'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Permis:</span>
                  <span className="text-slate-200">{client.licence_number || 'N/A'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Email:</span>
                  <span className="text-slate-200 truncate">{client.email || 'N/A'}</span>
                </div>
              </div>

              <div className="flex gap-2">
                <button className="btn-secondary flex-1 text-sm py-2">
                  <History size={14} className="inline mr-1" />
                  Historique
                </button>
                <button 
                  onClick={() => onNavigate('new-case', undefined, client.id)}
                  className="btn-primary flex-1 text-sm py-2"
                >
                  <Plus size={14} className="inline mr-1" />
                  Nouveau dossier
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
