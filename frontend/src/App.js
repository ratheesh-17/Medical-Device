import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Topbar from './components/Topbar';
import PredictPage from './pages/PredictPage';
import HistoryPage from './pages/HistoryPage';
import MetricsPage from './pages/MetricsPage';
import HealthPage from './pages/HealthPage';
import { getHealth } from './services/api';

export default function App() {
  const [healthStatus, setHealthStatus] = useState(null);

  useEffect(() => {
    getHealth()
      .then((r) => setHealthStatus(r.data.status))
      .catch(() => setHealthStatus('error'));
  }, []);

  return (
    <BrowserRouter>
      <Topbar healthStatus={healthStatus} />
      <Routes>
        <Route path="/" element={<PredictPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/metrics" element={<MetricsPage />} />
        <Route path="/health" element={<HealthPage onStatus={setHealthStatus} />} />
      </Routes>
      <footer>SentryMed · Cognizant NPN AI Hackathon · Medical Device Risk Intelligence</footer>
    </BrowserRouter>
  );
}
