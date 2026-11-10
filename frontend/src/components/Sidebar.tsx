import {
  Home,
  LayoutDashboard,
  FilePlus,
  FileSearch,
  BarChart3,
  ClipboardCheck,
  Shield,
  Activity,
  Database,
  Users,
  ChevronRight,
} from 'lucide-react';

export type Page =
  | 'home'
  | 'dashboard'
  | 'dataset'
  | 'clients'
  | 'new-case'
  | 'documents'
  | 'decision'
  | 'benchmark'
  | 'audit';

interface NavItem {
  id: Page;
  label: string;
  icon: React.ReactNode;
  gradient: string;
}

const NAV: NavItem[] = [
  { id: 'home',       label: 'Accueil',           icon: <Home size={20} />, gradient: 'from-blue-500 to-cyan-500' },
  { id: 'dashboard',  label: 'Tableau de bord',   icon: <LayoutDashboard size={20} />, gradient: 'from-violet-500 to-purple-500' },
  { id: 'dataset',    label: 'Dataset',           icon: <Database size={20} />, gradient: 'from-emerald-500 to-teal-500' },
  { id: 'clients',    label: 'Clients',           icon: <Users size={20} />, gradient: 'from-pink-500 to-rose-500' },
  { id: 'new-case',   label: 'Nouveau dossier',   icon: <FilePlus size={20} />, gradient: 'from-amber-500 to-orange-500' },
  { id: 'documents',  label: 'Documents',          icon: <FileSearch size={20} />, gradient: 'from-indigo-500 to-blue-500' },
  { id: 'decision',   label: 'Décision',           icon: <ClipboardCheck size={20} />, gradient: 'from-cyan-500 to-blue-500' },
  { id: 'benchmark',  label: 'Benchmark Science',  icon: <BarChart3 size={20} />, gradient: 'from-emerald-500 to-cyan-500' },
  { id: 'audit',      label: 'Audit & Conformité', icon: <Shield size={20} />, gradient: 'from-red-500 to-pink-500' },
];

interface SidebarProps {
  current: Page;
  onNavigate: (page: Page) => void;
  health?: 'healthy' | 'degraded' | 'unhealthy';
}

export default function Sidebar({ current, onNavigate, health }: SidebarProps) {
  const healthColor =
    health === 'healthy' ? 'text-emerald-400' :
    health === 'degraded' ? 'text-amber-400' : 'text-red-400';

  const healthBg =
    health === 'healthy' ? 'bg-emerald-400' :
    health === 'degraded' ? 'bg-amber-400' : 'bg-red-400';

  return (
    <aside className="w-72 shrink-0 bg-slate-900/80 backdrop-blur-xl border-r border-slate-700/30 flex flex-col h-screen">
      {/* Logo */}
      <div className="px-6 py-6 border-b border-slate-700/30">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600 to-cyan-600 flex items-center justify-center shadow-lg">
            <Activity size={24} className="text-white" />
          </div>
          <div>
            <p className="font-bold text-slate-100 text-lg leading-tight">UIP Platform</p>
            <p className="text-slate-500 text-xs">Underwriting Intelligence</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
        {NAV.map(item => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={current === item.id
              ? 'flex items-center gap-4 px-4 py-4 rounded-xl cursor-pointer transition-all duration-300 text-white font-medium w-full bg-gradient-to-r ' + item.gradient + ' shadow-lg scale-105'
              : 'flex items-center gap-4 px-4 py-4 rounded-xl cursor-pointer transition-all duration-300 text-slate-400 hover:text-slate-100 hover:bg-slate-800/50 w-full'
            }
          >
            <div className={`p-2 rounded-lg ${current === item.id ? 'bg-white/20' : 'bg-slate-800/50'}`}>
              {item.icon}
            </div>
            <span className="text-sm flex-1 text-left font-medium">{item.label}</span>
            {current === item.id && <ChevronRight size={16} />}
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-slate-700/30">
        <div className="flex items-center gap-3 text-sm">
          <span className={`w-3 h-3 rounded-full ${healthBg} animate-pulse`} />
          <span className={healthColor}>
            {health === 'healthy' ? 'Système opérationnel' : health === 'degraded' ? 'Dégradé' : 'Hors-ligne'}
          </span>
        </div>
        <p className="text-slate-600 text-xs mt-2">v1.0 · RGPD conforme</p>
      </div>
    </aside>
  );
}
