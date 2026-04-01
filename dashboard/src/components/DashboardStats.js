import React from 'react';
import { motion } from 'framer-motion';
import { BarChart3, Layers, GitCompare, Fingerprint } from 'lucide-react';

const statConfig = [
  { key: 'total_issues_analyzed', label: 'Tickets analysés', icon: BarChart3, color: '#1a1a2e' },
  { key: 'duplicate_groups_found', label: 'Groupes de doublons', icon: GitCompare, color: '#e65100' },
  { key: 'total_duplicate_issues', label: 'Tickets en doublon', icon: Layers, color: '#d32f2f' },
  { key: 'unique_issues', label: 'Tickets uniques', icon: Fingerprint, color: '#2e7d32' },
];

function AnimatedNumber({ value }) {
  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.5 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: 'spring', stiffness: 200, damping: 15 }}
    >
      {value}
    </motion.span>
  );
}

export default function DashboardStats({ data }) {
  return (
    <div className="stats-grid">
      {statConfig.map((stat, i) => {
        const Icon = stat.icon;
        return (
          <motion.div
            key={stat.key}
            className="stat-card glass-panel"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1, duration: 0.4 }}
          >
            <div className="stat-header">
              <span>{stat.label}</span>
              <Icon size={20} style={{ color: stat.color }} />
            </div>
            <div className="stat-value" style={{ color: stat.color }}>
              <AnimatedNumber value={data[stat.key]} />
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
