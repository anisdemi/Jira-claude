import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Wrench, Filter } from 'lucide-react';

function PriorityBadge({ priority }) {
  const map = { CRITICAL: 'badge-priority-critical', HIGH: 'badge-priority-high', MEDIUM: 'badge-priority-medium', LOW: 'badge-priority-low' };
  const labels = { CRITICAL: 'Critique', HIGH: 'Haute', MEDIUM: 'Moyenne', LOW: 'Basse' };
  return <span className={`badge ${map[priority] || 'badge-priority-medium'}`}>{labels[priority] || priority}</span>;
}

function ComplexityDots({ complexity }) {
  const levels = { Simple: 1, Medium: 2, Complex: 3 };
  const labels = { Simple: 'Simple', Medium: 'Moyenne', Complex: 'Complexe' };
  const level = levels[complexity] || 2;
  return (
    <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
      {[1, 2, 3].map(i => (
        <div
          key={i}
          style={{
            width: 8, height: 8, borderRadius: '50%',
            background: i <= level ? '#1a1a2e' : '#e5e5e3',
            transition: 'background 0.3s ease',
          }}
        />
      ))}
      <span style={{ marginLeft: '6px', color: '#6b6b7b', fontSize: '0.78rem' }}>{labels[complexity] || complexity}</span>
    </div>
  );
}

export default function UniqueIssues({ issues }) {
  const [filter, setFilter] = useState('ALL');

  const priorityLabels = { CRITICAL: 'Critique', HIGH: 'Haute', MEDIUM: 'Moyenne', LOW: 'Basse' };
  const priorities = ['ALL', ...new Set(issues.map(i => i.solution?.priority).filter(Boolean))];
  const filtered = filter === 'ALL' ? issues : issues.filter(i => i.solution?.priority === filter);

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '8px', color: '#1a1a2e' }}>
          Tickets uniques <span style={{ color: '#6b6b7b', fontWeight: 400 }}>({issues.length})</span>
        </h2>
        <p style={{ color: '#6b6b7b', marginBottom: '16px' }}>Tickets confirmés comme uniques — aucun doublon détecté.</p>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
          <Filter size={16} color="#6b6b7b" />
          {priorities.map(p => (
            <button
              key={p}
              className={`tab-btn ${filter === p ? 'active' : ''}`}
              onClick={() => setFilter(p)}
              style={{ fontSize: '0.85rem', padding: '6px 12px' }}
            >
              {p === 'ALL' ? 'Tous' : priorityLabels[p] || p}
            </button>
          ))}
        </div>
      </div>

      <div className="list-container">
        {filtered.map((issue, i) => (
          <motion.div
            key={issue.key}
            className="item-card glass-panel"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05, duration: 0.35 }}
          >
            <div className="item-header">
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap' }}>
                  <span className="issue-key">{issue.key}</span>
                  <PriorityBadge priority={issue.solution?.priority} />
                  <ComplexityDots complexity={issue.solution?.complexity} />
                </div>
                <h3 className="item-title">{issue.summary}</h3>
              </div>
            </div>

            {issue.solution && (
              <div className="solution-box">
                <div className="solution-title">
                  <Wrench size={16} style={{ color: '#1a1a2e' }} /> Solution
                </div>
                <p style={{ color: '#6b6b7b', fontSize: '0.9rem', lineHeight: 1.7 }}>
                  {issue.solution.description}
                </p>
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}
