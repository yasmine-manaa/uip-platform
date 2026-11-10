import { useState, useEffect } from 'react';
import { CheckCircle, AlertCircle, Loader2, User, Car, FileText, Shield, Users } from 'lucide-react';
import { api } from '../services/api';
import type { CaseCreate, Client } from '../types';
import type { Page } from '../components/Sidebar';

interface NewCasePageProps {
  onNavigate: (page: Page, caseId?: string) => void;
  selectedClientId?: string;
}

const DEFAULT_FORM: CaseCreate = {
  applicant: {
    full_name: '',
    driver_age: 35,
    licence_years: 14,
    usage: 'Commuting',
    postal_code: '75001',
    annual_mileage: 15000,
  },
  vehicle: {
    vehicle_model: 'Peugeot 208',
    vehicle_power: 6,
    vehicle_age: 5,
    vehicle_genre: 'VP',
    license_plate: 'AA-123-AA',
  },
  claims_summary: {
    bonus_malus: 0.85,
    prior_claims_count: 0,
    cancelled_by_previous_insurer: false,
  },
  coverage_requested: 'RC_TIERS_COMPLET',
  area_density: 3,
};

function Field({
  label, name, value, onChange, type = 'text', min, max, step,
}: {
  label: string;
  name: string;
  value: string | number;
  onChange: (val: string) => void;
  type?: string;
  min?: number;
  max?: number;
  step?: number;
}) {
  return (
    <div>
      <label className="label">{label}</label>
      <input
        type={type}
        name={name}
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={e => onChange(e.target.value)}
        className="input-field"
      />
    </div>
  );
}

export default function NewCasePage({ onNavigate, selectedClientId }: NewCasePageProps) {
  const [form, setForm] = useState<CaseCreate>(DEFAULT_FORM);
  const [step, setStep] = useState<'idle' | 'creating' | 'analyzing' | 'done' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [caseId, setCaseId] = useState<string | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [isRenewal, setIsRenewal] = useState(false);

  // Load clients
  useEffect(() => {
    api.listClients().then(setClients).catch(console.error);
  }, []);

  // Set client if selected
  useEffect(() => {
    if (selectedClientId) {
      const client = clients.find(c => c.id === selectedClientId);
      if (client) {
        setSelectedClient(client);
        setIsRenewal(true);
        // Pre-fill form with client data
        setForm(prev => ({
          ...prev,
          applicant: {
            ...prev.applicant,
            full_name: client.full_name,
            driver_age: client.driver_age || prev.applicant.driver_age,
            licence_years: prev.applicant.licence_years,
          }
        }));
      }
    }
  }, [selectedClientId, clients]);

  const set = (path: string, value: unknown) => {
    setForm(prev => {
      const clone = JSON.parse(JSON.stringify(prev)) as CaseCreate;
      const parts = path.split('.');
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      let cur: any = clone;
      for (let i = 0; i < parts.length - 1; i++) cur = cur[parts[i]];
      cur[parts[parts.length - 1]] = value;
      return clone;
    });
  };

  const handleSubmit = async () => {
    setStep('creating');
    setError(null);
    try {
      // Create or get client
      let clientId = selectedClientId;
      if (!clientId) {
        const client = await api.createClient({
          full_name: form.applicant.full_name,
          driver_age: form.applicant.driver_age,
          licence_number: form.applicant.licence_years?.toString(),
        });
        clientId = client.id;
      }

      const created = await api.createCase(form);
      setCaseId(created.id);
      setStep('analyzing');
      await api.startAnalysis(created.id);
      setStep('done');
    } catch (e) {
      setError(String(e));
      setStep('error');
    }
  };

  if (step === 'done' && caseId) {
    return (
      <div className="p-8 flex flex-col items-center justify-center h-full gap-6 animate-fadeIn">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-600 to-emerald-700 flex items-center justify-center shadow-lg">
          <CheckCircle size={40} className="text-white" />
        </div>
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold text-slate-100">Dossier créé et analysé !</h2>
          <p className="text-slate-400">L'analyse multi-agents est en cours ou terminée.</p>
        </div>
        <div className="flex gap-4">
          <button onClick={() => onNavigate('decision', caseId)} className="btn-primary">
            Voir la décision
          </button>
          <button
            onClick={() => { setForm(DEFAULT_FORM); setStep('idle'); }}
            className="btn-secondary"
          >
            Nouveau dossier
          </button>
        </div>
      </div>
    );
  }

  const busy = step === 'creating' || step === 'analyzing';

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="animate-fadeIn">
        <h1 className="text-3xl font-bold gradient-text">
          {isRenewal ? 'Renouvellement de dossier' : 'Nouveau dossier'}
        </h1>
        <p className="text-slate-400 mt-2">
          {isRenewal 
            ? `Renouvellement pour ${selectedClient?.full_name}`
            : 'Saisissez les informations de l\'assuré pour lancer l\'analyse multi-agents.'
          }
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-950/50 border border-red-700/50 rounded-xl text-red-300 flex items-center gap-3">
          <AlertCircle size={20} /> {error}
        </div>
      )}

      {/* Client Selection */}
      {!isRenewal && (
        <div className="card animate-slideIn" style={{ animationDelay: '0.1s' }}>
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 rounded-xl bg-gradient-to-br from-pink-500 to-rose-600">
              <Users size={24} className="text-white" />
            </div>
            <h2 className="text-xl font-semibold text-slate-200">Client</h2>
          </div>
          <div>
            <label className="label">Sélectionner un client existant (optionnel)</label>
            <select
              className="input-field"
              value={selectedClient?.id || ''}
              onChange={e => {
                const client = clients.find(c => c.id === e.target.value);
                if (client) {
                  setSelectedClient(client);
                  setIsRenewal(true);
                  setForm(prev => ({
                    ...prev,
                    applicant: {
                      ...prev.applicant,
                      full_name: client.full_name,
                      driver_age: client.driver_age || prev.applicant.driver_age,
                    }
                  }));
                }
              }}
            >
              <option value="">— Nouveau client —</option>
              {clients.map(c => (
                <option key={c.id} value={c.id}>{c.full_name} ({c.client_reference})</option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Section 1 — Assuré */}
      <div className="card animate-slideIn" style={{ animationDelay: '0.2s' }}>
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600">
            <User size={24} className="text-white" />
          </div>
          <h2 className="text-xl font-semibold text-slate-200">1. Identification de l'assuré</h2>
        </div>
        <div className="space-y-4">
          <Field label="Nom complet" name="full_name" value={form.applicant.full_name}
            onChange={v => set('applicant.full_name', v)} />
          <div className="grid grid-cols-2 gap-4">
            <Field label="Âge" name="driver_age" value={form.applicant.driver_age} type="number" min={18} max={100}
              onChange={v => set('applicant.driver_age', Number(v))} />
            <Field label="Années de permis" name="licence_years" value={form.applicant.licence_years}
              type="number" min={0} max={60}
              onChange={v => set('applicant.licence_years', Number(v))} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Usage du véhicule</label>
              <select
                className="input-field"
                value={form.applicant.usage}
                onChange={e => set('applicant.usage', e.target.value)}
              >
                {['Private', 'Commuting', 'Professional', 'Taxi_VTC'].map(u => (
                  <option key={u} value={u}>{u}</option>
                ))}
              </select>
            </div>
            <Field label="Code postal" name="postal_code" value={form.applicant.postal_code}
              onChange={v => set('applicant.postal_code', v)} />
          </div>
          <Field label="Kilométrage annuel" name="annual_mileage" value={form.applicant.annual_mileage || 15000}
            type="number" min={4000} max={70000}
            onChange={v => set('applicant.annual_mileage', Number(v))} />
        </div>
      </div>

      {/* Section 2 — Véhicule */}
      <div className="card animate-slideIn" style={{ animationDelay: '0.3s' }}>
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 rounded-xl bg-gradient-to-br from-violet-500 to-violet-600">
            <Car size={24} className="text-white" />
          </div>
          <h2 className="text-xl font-semibold text-slate-200">2. Véhicule assuré</h2>
        </div>
        <div className="space-y-4">
          <Field label="Modèle" name="vehicle_model" value={form.vehicle.vehicle_model}
            onChange={v => set('vehicle.vehicle_model', v)} />
          <div className="grid grid-cols-3 gap-4">
            <Field label="Puissance fiscale (CV)" name="vehicle_power" value={form.vehicle.vehicle_power} type="number" min={3} max={25}
              onChange={v => set('vehicle.vehicle_power', Number(v))} />
            <Field label="Âge du véhicule (ans)" name="vehicle_age" value={form.vehicle.vehicle_age} type="number" min={0} max={30}
              onChange={v => set('vehicle.vehicle_age', Number(v))} />
            <div>
              <label className="label">Genre</label>
              <select
                className="input-field"
                value={form.vehicle.vehicle_genre}
                onChange={e => set('vehicle.vehicle_genre', e.target.value)}
              >
                {['VP', 'VUL', 'CAMION', 'MOTO', 'SCOOTER'].map(g => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
            </div>
          </div>
          <Field label="Immatriculation" name="license_plate" value={form.vehicle.license_plate || ''}
            onChange={v => set('vehicle.license_plate', v)} />
        </div>
      </div>

      {/* Section 3 — Sinistralité */}
      <div className="card animate-slideIn" style={{ animationDelay: '0.4s' }}>
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600">
            <FileText size={24} className="text-white" />
          </div>
          <h2 className="text-xl font-semibold text-slate-200">3. Historique sinistres</h2>
        </div>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Coefficient Bonus-Malus" name="bonus_malus" value={form.claims_summary.bonus_malus}
              type="number" min={0.5} max={2.5} step={0.01}
              onChange={v => set('claims_summary.bonus_malus', Number(v))} />
            <Field label="Sinistres (3 ans)" name="prior_claims_count"
              value={form.claims_summary.prior_claims_count} type="number" min={0} max={10}
              onChange={v => set('claims_summary.prior_claims_count', Number(v))} />
          </div>
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="prior_cancel"
              checked={form.claims_summary.cancelled_by_previous_insurer || false}
              onChange={e => set('claims_summary.cancelled_by_previous_insurer', e.target.checked)}
              className="w-5 h-5 rounded"
            />
            <label htmlFor="prior_cancel" className="text-sm text-slate-300">
              Résiliation antérieure par un assureur
            </label>
          </div>
        </div>
      </div>

      {/* Section 4 — Garanties */}
      <div className="card animate-slideIn" style={{ animationDelay: '0.5s' }}>
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 rounded-xl bg-gradient-to-br from-amber-500 to-amber-600">
            <Shield size={24} className="text-white" />
          </div>
          <h2 className="text-xl font-semibold text-slate-200">4. Garanties souhaitées</h2>
        </div>
        <div className="space-y-4">
          <div>
            <label className="label">Niveau de couverture</label>
            <select
              className="input-field"
              value={form.coverage_requested}
              onChange={e => set('coverage_requested', e.target.value)}
            >
              {[
                ['RC_TIERS', 'Responsabilité Civile Tiers'],
                ['RC_TIERS_COMPLET', 'Tiers Complet'],
                ['TOUS_RISQUES', 'Tous Risques'],
              ].map(([val, label]) => (
                <option key={val} value={val}>{label}</option>
              ))}
            </select>
          </div>
          <Field label="Densité de zone (1-6)" name="area_density" value={form.area_density || 3}
            type="number" min={1} max={6}
            onChange={v => set('area_density', Number(v))} />
        </div>
      </div>

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={busy || !form.applicant.full_name}
        className="btn-primary w-full flex items-center justify-center gap-3 py-4 text-lg disabled:opacity-50 disabled:cursor-not-allowed animate-fadeIn"
        style={{ animationDelay: '0.6s' }}
      >
        {busy ? (
          <>
            <Loader2 size={20} className="animate-spin" />
            {step === 'creating' ? 'Création du dossier…' : 'Lancement de l\'analyse…'}
          </>
        ) : (
          <>
            <CheckCircle size={20} />
            {isRenewal ? 'Créer le renouvellement' : 'Créer et analyser le dossier'}
          </>
        )}
      </button>
    </div>
  );
}
