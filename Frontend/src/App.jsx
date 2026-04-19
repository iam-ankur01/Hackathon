import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Home from './pages/Home';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Results from './pages/Results';
import Profile from './pages/Profile';
import Roadmap from './pages/Roadmap';
import Coach from './pages/Coach';
import Progress from './pages/Progress';
import JobMatches from './pages/JobMatches';
import History from './pages/History';
import { loadSession, clearSession } from './lib/api';

function AppLayout({ children, user, onLogout }) {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Navbar user={user} onLogout={onLogout} />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [booted, setBooted] = useState(false);

  useEffect(() => {
    const session = loadSession();
    if (session) setUser(session.user);
    setBooted(true);
  }, []);

  const handleLogout = () => { clearSession(); setUser(null); };

  if (!booted) return null;

  if (!user) {
    return (
      <Router>
        <Routes>
          <Route path="/" element={<Home onLogin={setUser} />} />
          <Route path="/login" element={<Login onLogin={setUser} />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Router>
    );
  }
  return (
    <Router>
      <Routes>
        <Route path="/" element={<AppLayout user={user} onLogout={handleLogout}><Dashboard user={user} /></AppLayout>} />
        <Route path="/dashboard" element={<AppLayout user={user} onLogout={handleLogout}><Dashboard user={user} /></AppLayout>} />
        <Route path="/results" element={<AppLayout user={user} onLogout={handleLogout}><Results /></AppLayout>} />
        <Route path="/results/:id" element={<AppLayout user={user} onLogout={handleLogout}><Results /></AppLayout>} />
        <Route path="/profile" element={<AppLayout user={user} onLogout={handleLogout}><Profile user={user} setUser={setUser} /></AppLayout>} />
        <Route path="/roadmap" element={<AppLayout user={user} onLogout={handleLogout}><Roadmap /></AppLayout>} />
        <Route path="/coach" element={<AppLayout user={user} onLogout={handleLogout}><Coach user={user} /></AppLayout>} />
        <Route path="/progress" element={<AppLayout user={user} onLogout={handleLogout}><Progress user={user} /></AppLayout>} />
        <Route path="/jobs" element={<AppLayout user={user} onLogout={handleLogout}><JobMatches /></AppLayout>} />
        <Route path="/history" element={<AppLayout user={user} onLogout={handleLogout}><History /></AppLayout>} />
        <Route path="*" element={<Navigate to="/dashboard" />} />
      </Routes>
    </Router>
  );
}
export default App;
