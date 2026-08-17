import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Topbar from './components/Topbar';
import LoginPage from './pages/LoginPage';
import PredictPage from './pages/PredictPage';
import HistoryPage from './pages/HistoryPage';
import MetricsPage from './pages/MetricsPage';
import HealthPage from './pages/HealthPage';
import MfrDashboardPage from './pages/mfr/MfrDashboardPage';
import { getHealth } from './services/api';

function AppRoutes() {
  const { user, loading } = useAuth();
  const [healthStatus, setHealthStatus] = useState(null);

  useEffect(() => {
    getHealth()
      .then((r) => setHealthStatus(r.data.status))
      .catch(() => setHealthStatus('error'));
  }, []);

  if (loading) return <div className="spinner-center"><div className="spinner spinner-lg" /></div>;

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  if (user.role === 'manufacturer') {
    return (
      <>
        <Topbar healthStatus={healthStatus} />
        <Routes>
          <Route path="/manufacturer" element={<MfrDashboardPage />} />
          <Route path="*" element={<Navigate to="/manufacturer" replace />} />
        </Routes>
        <footer>SentryMed · Cognizant NPN AI Hackathon · Medical Device Risk Intelligence</footer>
      </>
    );
  }

  return (
    <>
      <Topbar healthStatus={healthStatus} />
      <Routes>
        <Route path="/" element={<PredictPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/metrics" element={<MetricsPage />} />
        <Route path="/health" element={<HealthPage onStatus={setHealthStatus} />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <footer>SentryMed · Cognizant NPN AI Hackathon · Medical Device Risk Intelligence</footer>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
