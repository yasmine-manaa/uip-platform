import { Activity, Users, FileText, Shield, BarChart3, ChevronRight, Database, Zap, Globe } from 'lucide-react';
import type { Page } from '../components/Sidebar';

interface WelcomePageProps {
  onNavigate: (page: Page) => void;
}

export default function WelcomePage({ onNavigate }: WelcomePageProps) {
  const features = [
    {
      icon: <Users size={32} className="text-blue-400" />,
      title: 'Gestion des dossiers',
      description: 'Créez et suivez les dossiers d\'assurance automobile avec une interface intuitive',
      page: 'new-case' as Page,
      action: 'Créer un dossier',
      gradient: 'from-blue-500/20 to-blue-600/10'
    },
    {
      icon: <FileText size={32} className="text-violet-400" />,
      title: 'Analyse de documents',
      description: 'Téléchargez et analysez automatiquement les documents d\'assurance',
      page: 'documents' as Page,
      action: 'Gérer les documents',
      gradient: 'from-violet-500/20 to-violet-600/10'
    },
    {
      icon: <BarChart3 size={32} className="text-emerald-400" />,
      title: 'Décision algorithmique',
      description: 'Consultez les recommandations des agents IA avec explications détaillées',
      page: 'decision' as Page,
      action: 'Voir les décisions',
      gradient: 'from-emerald-500/20 to-emerald-600/10'
    },
    {
      icon: <Shield size={32} className="text-amber-400" />,
      title: 'Audit & Conformité',
      description: 'Suivez la piste d\'audit et assurez la conformité RGPD',
      page: 'audit' as Page,
      action: 'Voir l\'audit',
      gradient: 'from-amber-500/20 to-amber-600/10'
    }
  ];

  const stats = [
    { label: 'Agents IA', value: '6', icon: <Users size={20} />, color: 'text-blue-400' },
    { label: 'Modèles actuariels', value: '4', icon: <BarChart3 size={20} />, color: 'text-emerald-400' },
    { label: 'Variables', value: '12', icon: <Database size={20} />, color: 'text-violet-400' },
    { label: 'Traçabilité', value: '100%', icon: <Shield size={20} />, color: 'text-amber-400' },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-12">
      {/* Hero Section */}
      <div className="text-center space-y-6 animate-fadeIn">
        <div className="flex items-center justify-center gap-4">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-600 flex items-center justify-center shadow-2xl">
            <Activity size={40} className="text-white" />
          </div>
        </div>
        <div className="space-y-3">
          <h1 className="text-5xl font-bold gradient-text">
            Underwriting Intelligence Platform
          </h1>
          <p className="text-xl text-slate-400 max-w-3xl mx-auto leading-relaxed">
            Plateforme multi-agents de nouvelle génération pour l'aide à la souscription 
            d'assurance automobile. Combinez intelligence artificielle et expertise actuarielle.
          </p>
        </div>
        <div className="flex items-center justify-center gap-8 text-sm text-slate-500">
          <div className="flex items-center gap-2">
            <Zap size={16} className="text-amber-400" />
            <span>GLM Poisson</span>
          </div>
          <div className="flex items-center gap-2">
            <Zap size={16} className="text-amber-400" />
            <span>GLM Gamma</span>
          </div>
          <div className="flex items-center gap-2">
            <Zap size={16} className="text-amber-400" />
            <span>XGBoost</span>
          </div>
          <div className="flex items-center gap-2">
            <Zap size={16} className="text-amber-400" />
            <span>RAG</span>
          </div>
          <div className="flex items-center gap-2">
            <Zap size={16} className="text-amber-400" />
            <span>LangGraph</span>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <div key={i} className="card card-hover text-center animate-slideIn" style={{ animationDelay: `${i * 0.1}s` }}>
            <div className="flex items-center justify-center mb-3">
              <div className={`p-3 rounded-xl bg-slate-800 ${stat.color}`}>
                {stat.icon}
              </div>
            </div>
            <p className={`text-3xl font-bold ${stat.color} mb-1`}>{stat.value}</p>
            <p className="text-sm text-slate-400">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {features.map((feature, i) => (
          <div 
            key={i} 
            className={`card card-hover cursor-pointer group animate-slideIn bg-gradient-to-br ${feature.gradient} border-slate-700/50`}
            style={{ animationDelay: `${(i + 4) * 0.1}s` }}
            onClick={() => onNavigate(feature.page)}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="p-4 rounded-xl bg-slate-800/50 backdrop-blur-sm">
                {feature.icon}
              </div>
              <ChevronRight size={24} className="text-slate-600 group-hover:text-blue-400 transition-colors" />
            </div>
            <h3 className="font-semibold text-slate-200 mb-2 text-lg">{feature.title}</h3>
            <p className="text-sm text-slate-400 mb-4 leading-relaxed">{feature.description}</p>
            <button className="text-sm text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1">
              {feature.action} <ChevronRight size={14} />
            </button>
          </div>
        ))}
      </div>

      {/* Quick Start Guide */}
      <div className="card animate-fadeIn" style={{ animationDelay: '0.8s' }}>
        <h2 className="text-2xl font-bold text-slate-100 mb-6 flex items-center gap-3">
          <Globe size={24} className="text-blue-400" />
          Guide de démarrage rapide
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center text-white font-bold">1</div>
              <h3 className="font-semibold text-slate-200">Créer un dossier</h3>
            </div>
            <p className="text-sm text-slate-400 leading-relaxed">
              Remplissez le formulaire avec les informations de l'assuré et du véhicule
            </p>
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-600 to-violet-700 flex items-center justify-center text-white font-bold">2</div>
              <h3 className="font-semibold text-slate-200">Télécharger les documents</h3>
            </div>
            <p className="text-sm text-slate-400 leading-relaxed">
              Ajoutez les documents nécessaires (permis, carte grise, attestation)
            </p>
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-600 to-emerald-700 flex items-center justify-center text-white font-bold">3</div>
              <h3 className="font-semibold text-slate-200">Lancer l'analyse</h3>
            </div>
            <p className="text-sm text-slate-400 leading-relaxed">
              Les agents IA analysent automatiquement le dossier
            </p>
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-amber-600 to-amber-700 flex items-center justify-center text-white font-bold">4</div>
              <h3 className="font-semibold text-slate-200">Valider la décision</h3>
            </div>
            <p className="text-sm text-slate-400 leading-relaxed">
              Un souscripteur valide ou modifie la recommandation algorithmique
            </p>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="card card-hover bg-gradient-to-br from-blue-900/30 to-cyan-900/30 border-blue-700/30 animate-fadeIn" style={{ animationDelay: '1s' }}>
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-bold text-slate-100">Prêt à commencer ?</h2>
          <p className="text-slate-400">Créez votre premier dossier et découvrez la puissance de l'IA actuarielle</p>
          <button 
            onClick={() => onNavigate('new-case')}
            className="btn-primary text-lg px-8 py-4"
          >
            <span className="flex items-center gap-2">
              <Users size={20} />
              Créer un dossier
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
