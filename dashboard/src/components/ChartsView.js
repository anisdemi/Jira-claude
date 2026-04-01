import React from 'react';
import { motion } from 'framer-motion';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
} from 'recharts';

const COLORS = ['#ffcc00', '#1a1a2e', '#e65100', '#2e7d32', '#5c6bc0', '#d32f2f', '#00838f', '#6d4c41'];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: '#ffffff',
        border: '1px solid #e5e5e3',
        borderRadius: '8px',
        padding: '10px 14px',
        color: '#1a1a2e',
        fontSize: '0.9rem',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
      }}>
        <p style={{ fontWeight: 600 }}>{label || payload[0].name}</p>
        <p style={{ color: payload[0].color || '#1a1a2e', fontWeight: 700 }}>{payload[0].value}</p>
      </div>
    );
  }
  return null;
};

export default function ChartsView({ duplicateGroups, uniqueIssues }) {
  // Confidence distribution
  const confidenceMap = {};
  duplicateGroups.forEach(g => {
    const label = g.confidence === 'HIGH' ? 'Élevée' : g.confidence === 'MEDIUM' ? 'Moyenne' : 'Faible';
    confidenceMap[label] = (confidenceMap[label] || 0) + 1;
  });
  const confidenceData = Object.entries(confidenceMap).map(([name, value]) => ({ name, value }));

  // Priority distribution
  const priorityMap = {};
  const priorityLabels = { CRITICAL: 'Critique', HIGH: 'Haute', MEDIUM: 'Moyenne', LOW: 'Basse' };
  duplicateGroups.forEach(g => {
    const p = priorityLabels[g.solution?.priority] || 'Inconnue';
    priorityMap[p] = (priorityMap[p] || 0) + 1;
  });
  uniqueIssues.forEach(u => {
    const p = priorityLabels[u.solution?.priority] || 'Inconnue';
    priorityMap[p] = (priorityMap[p] || 0) + 1;
  });
  const priorityData = Object.entries(priorityMap).map(([name, value]) => ({ name, value }));

  // Complexity distribution
  const complexityLabels = { Simple: 'Simple', Medium: 'Moyenne', Complex: 'Complexe' };
  const complexityMap = {};
  duplicateGroups.forEach(g => {
    const c = complexityLabels[g.solution?.complexity] || 'Inconnue';
    complexityMap[c] = (complexityMap[c] || 0) + 1;
  });
  uniqueIssues.forEach(u => {
    const c = complexityLabels[u.solution?.complexity] || 'Inconnue';
    complexityMap[c] = (complexityMap[c] || 0) + 1;
  });
  const complexityData = Object.entries(complexityMap).map(([name, value]) => ({ name, value }));

  // Issues per duplicate group
  const groupSizeData = duplicateGroups.map(g => ({
    name: `Grp ${g.group_id}`,
    issues: g.issues.length,
  }));

  return (
    <div className="charts-grid">
      <motion.div className="chart-card glass-panel" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.2 }}>
        <h3 className="chart-title">Niveau de confiance</h3>
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={confidenceData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={5}
              dataKey="value"
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              animationBegin={0}
              animationDuration={800}
            >
              {confidenceData.map((_, i) => (
                <Cell key={`cell-${i}`} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </motion.div>

      <motion.div className="chart-card glass-panel" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.3 }}>
        <h3 className="chart-title">Répartition par priorité</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={priorityData} barSize={40}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e3" />
            <XAxis dataKey="name" tick={{ fill: '#6b6b7b', fontSize: 12 }} />
            <YAxis tick={{ fill: '#6b6b7b', fontSize: 12 }} allowDecimals={false} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="value" radius={[6, 6, 0, 0]} animationDuration={800}>
              {priorityData.map((entry, i) => {
                const colorMap = { Critique: '#d32f2f', Haute: '#e65100', Moyenne: '#5c6bc0', Basse: '#2e7d32' };
                return <Cell key={`pr-${i}`} fill={colorMap[entry.name] || COLORS[i]} />;
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </motion.div>

      <motion.div className="chart-card glass-panel" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.4 }}>
        <h3 className="chart-title">Répartition par complexité</h3>
        <ResponsiveContainer width="100%" height={280}>
          <RadarChart cx="50%" cy="50%" outerRadius="70%" data={complexityData}>
            <PolarGrid stroke="#e5e5e3" />
            <PolarAngleAxis dataKey="name" tick={{ fill: '#6b6b7b', fontSize: 12 }} />
            <PolarRadiusAxis tick={{ fill: '#6b6b7b', fontSize: 10 }} />
            <Radar dataKey="value" stroke="#1a1a2e" fill="#ffcc00" fillOpacity={0.35} animationDuration={800} />
            <Tooltip content={<CustomTooltip />} />
          </RadarChart>
        </ResponsiveContainer>
      </motion.div>

      <motion.div className="chart-card glass-panel" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.5 }}>
        <h3 className="chart-title">Tickets par groupe de doublons</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={groupSizeData} barSize={32}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e3" />
            <XAxis dataKey="name" tick={{ fill: '#6b6b7b', fontSize: 12 }} />
            <YAxis tick={{ fill: '#6b6b7b', fontSize: 12 }} allowDecimals={false} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="issues" radius={[6, 6, 0, 0]} animationDuration={800}>
              {groupSizeData.map((_, i) => (
                <Cell key={`gs-${i}`} fill={COLORS[i % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </motion.div>
    </div>
  );
}
