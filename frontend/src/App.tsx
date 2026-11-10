import { useEffect, useState } from 'react';
import Sidebar, { type Page } from './components/Sidebar';
import WelcomePage from './pages/WelcomePage';
import DashboardPage from './pages/DashboardPage';
import DatasetPage from './pages/DatasetPage';
import ClientsPage from './pages/ClientsPage';
import NewCasePage from './pages/NewCasePage';
import DocumentsPage from './pages/DocumentsPage';
import DecisionPage from './pages/DecisionPage';
import BenchmarkPage from './pages/BenchmarkPage';
import AuditPage from './pages/AuditPage';
import { api } from './services/api';

export default function App() {
  const [page, setPage] = useState<Page>('home');
  const [activeCaseId, setActiveCaseId] = useState<string | null>(null);
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);
  const [health, setHealth] = useState<'healthy' | 'degraded' | 'unhealthy'>('degraded');

  useEffect(() => {
    api.getHealth()
      .then(h => setHealth(h.status === 'UP' ? 'healthy' : 'unhealthy'))
      .catch(() => setHealth('unhealthy'));
  }, []);

  const navigate = (p: Page, caseId?: string, clientId?: string) => {
    if (caseId) setActiveCaseId(caseId);
    if (clientId) setSelectedClientId(clientId);
    setPage(p);
  };

  const renderPage = () => {
    switch (page) {
      case 'home':       return <WelcomePage onNavigate={navigate} />;
      case 'dashboard':  return <DashboardPage onNavigate={navigate} />;
      case 'dataset':    return <DatasetPage />;
      case 'clients':    return <ClientsPage onNavigate={navigate} />;
      case 'new-case':   return <NewCasePage onNavigate={navigate} selectedClientId={selectedClientId} />;
      case 'documents':  return <DocumentsPage activeCaseId={activeCaseId} />;
      case 'decision':   return <DecisionPage activeCaseId={activeCaseId} setActiveCaseId={setActiveCaseId} />;
      case 'benchmark':  return <BenchmarkPage />;
      case 'audit':      return <AuditPage activeCaseId={activeCaseId} setActiveCaseId={setActiveCaseId} />;
      default:           return <WelcomePage onNavigate={navigate} />;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar current={page} onNavigate={navigate} health={health} />
      <main className="flex-1 overflow-y-auto">
        {renderPage()}
      </main>
    </div>
  );
}
