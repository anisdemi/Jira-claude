import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LayoutDashboard, Copy, FileBadge, Activity, Menu, X } from 'lucide-react';

import DashboardStats from './components/DashboardStats';
import ChartsView from './components/ChartsView';
import DuplicateGroups from './components/DuplicateGroups';
import UniqueIssues from './components/UniqueIssues';

import reportData from './data/report.json';

function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [menuOpen, setMenuOpen] = useState(false);

  const switchTab = (tab) => {
    setActiveTab(tab);
    setMenuOpen(false);
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <motion.div
            key="overview"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <DashboardStats data={reportData.analysis_summary} />
            <ChartsView duplicateGroups={reportData.duplicate_groups} uniqueIssues={reportData.unique_issues} />
          </motion.div>
        );
      case 'duplicates':
        return (
          <motion.div
            key="duplicates"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <DuplicateGroups groups={reportData.duplicate_groups} />
          </motion.div>
        );
      case 'unique':
        return (
          <motion.div
            key="unique"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <UniqueIssues issues={reportData.unique_issues} />
          </motion.div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="layout">
      {/* Mobile top bar */}
      <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)}>
        {menuOpen ? <X size={22} /> : <Menu size={22} />}
        <span>Jira Analyzer</span>
      </button>

      <aside
        className={`sidebar glass-panel ${menuOpen ? 'open' : ''}`}
        style={{ borderRadius: 0, borderTop: 0, borderBottom: 0, borderLeft: 0 }}
      >
        <div className="logo-container text-gradient" style={{ color: '#ffcc00' }}>
          <Activity size={28} />
          <span>Jira Analyzer</span>
        </div>

        <nav className="nav-links" style={{ marginTop: '32px' }}>
          <div
            className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => switchTab('overview')}
          >
            <LayoutDashboard size={20} />
            <span>Vue d'ensemble</span>
          </div>
          <div
            className={`nav-item ${activeTab === 'duplicates' ? 'active' : ''}`}
            onClick={() => switchTab('duplicates')}
          >
            <Copy size={20} />
            <span>Groupes de doublons</span>
          </div>
          <div
            className={`nav-item ${activeTab === 'unique' ? 'active' : ''}`}
            onClick={() => switchTab('unique')}
          >
            <FileBadge size={20} />
            <span>Tickets uniques</span>
          </div>
        </nav>
      </aside>

      {/* Overlay to close menu on mobile */}
      {menuOpen && (
        <div
          onClick={() => setMenuOpen(false)}
          style={{
            position: 'fixed', top: 56, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.3)', zIndex: 14,
          }}
        />
      )}

      <main className="main-content">
        <header className="page-header">
          <motion.h1
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="page-title text-gradient"
          >
            Tableau de bord — Analyse des tickets
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="page-subtitle"
          >
            Détection intelligente des doublons et recommandations de résolution
          </motion.p>
        </header>

        <AnimatePresence mode="wait">
          {renderContent()}
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;
