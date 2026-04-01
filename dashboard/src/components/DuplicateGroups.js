import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, AlertTriangle, Lightbulb, Star, Wrench } from 'lucide-react';

function ConfidenceBadge({ confidence }) {
  const labels = { HIGH: 'Élevée', MEDIUM: 'Moyenne', LOW: 'Faible' };
  const colors = {
    HIGH: { bg: 'rgba(46,125,50,0.08)', color: '#2e7d32', border: 'rgba(46,125,50,0.2)' },
    MEDIUM: { bg: 'rgba(230,81,0,0.08)', color: '#e65100', border: 'rgba(230,81,0,0.2)' },
    LOW: { bg: 'rgba(211,47,47,0.08)', color: '#d32f2f', border: 'rgba(211,47,47,0.2)' },
  };
  const c = colors[confidence] || colors.MEDIUM;
  return (
    <span className="badge" style={{ background: c.bg, color: c.color, border: `1px solid ${c.border}` }}>
      {labels[confidence] || confidence}
    </span>
  );
}

function PriorityBadge({ priority }) {
  const map = { CRITICAL: 'badge-priority-critical', HIGH: 'badge-priority-high', MEDIUM: 'badge-priority-medium', LOW: 'badge-priority-low' };
  const labels = { CRITICAL: 'Critique', HIGH: 'Haute', MEDIUM: 'Moyenne', LOW: 'Basse' };
  return <span className={`badge ${map[priority] || 'badge-priority-medium'}`}>{labels[priority] || priority}</span>;
}

function GroupCard({ group, index }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      className="item-card glass-panel"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.4 }}
    >
      <div className="item-header" style={{ cursor: 'pointer' }} onClick={() => setExpanded(!expanded)}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap' }}>
            <span style={{ color: '#1a1a2e', fontWeight: 800, fontSize: '0.85rem', background: '#ffcc00', padding: '2px 10px', borderRadius: '4px' }}>GROUPE {group.group_id}</span>
            <ConfidenceBadge confidence={group.confidence} />
            <PriorityBadge priority={group.solution?.priority} />
            <span className="badge" style={{ background: 'rgba(26,26,46,0.06)', color: '#1a1a2e', border: '1px solid rgba(26,26,46,0.12)' }}>
              {group.issues.length} tickets
            </span>
          </div>
          <h3 className="item-title">{group.theme}</h3>
        </div>
        <motion.div animate={{ rotate: expanded ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown size={24} color="#6b6b7b" />
        </motion.div>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            style={{ overflow: 'hidden' }}
          >
            {/* Similarity explanation */}
            <div style={{ padding: '16px', background: '#fafaf8', borderRadius: '8px', marginBottom: '16px', border: '1px solid #eeeeec' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: '#e65100', fontWeight: 700, fontSize: '0.9rem' }}>
                <AlertTriangle size={16} /> Analyse de similarité
              </div>
              <p style={{ color: '#6b6b7b', fontSize: '0.9rem', lineHeight: 1.7 }}>{group.similarity_explanation}</p>
            </div>

            {/* Child issues */}
            <div className="child-issues">
              {group.issues.map(issue => (
                <div key={issue.key} className="child-issue">
                  <span className="issue-key">{issue.key}</span>
                  <span style={{ color: '#6b6b7b', fontSize: '0.9rem', flex: 1 }}>{issue.summary}</span>
                  {issue.key === group.recommended_primary && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#2e7d32', fontSize: '0.78rem', fontWeight: 700, whiteSpace: 'nowrap' }}>
                      <Star size={14} /> PRINCIPAL
                    </span>
                  )}
                </div>
              ))}
            </div>

            {/* Recommended action */}
            <div style={{ marginTop: '16px', padding: '16px', background: 'rgba(46,125,50,0.04)', borderRadius: '8px', borderLeft: '3px solid #2e7d32' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: '#2e7d32', fontWeight: 700, fontSize: '0.9rem' }}>
                <Lightbulb size={16} /> Action recommandée
              </div>
              <p style={{ color: '#6b6b7b', fontSize: '0.9rem', lineHeight: 1.7 }}>{group.recommended_action}</p>
            </div>

            {/* Solution */}
            {group.solution && (
              <div className="solution-box">
                <div className="solution-title">
                  <Wrench size={16} style={{ color: '#1a1a2e' }} /> Solution proposée
                  <span style={{ marginLeft: 'auto', fontSize: '0.78rem', color: '#6b6b7b' }}>
                    Complexité : {group.solution.complexity === 'Simple' ? 'Simple' : group.solution.complexity === 'Medium' ? 'Moyenne' : 'Complexe'}
                  </span>
                </div>
                <p style={{ color: '#6b6b7b', fontSize: '0.9rem', lineHeight: 1.7, marginBottom: '12px' }}>{group.solution.description}</p>
                <details style={{ cursor: 'pointer' }}>
                  <summary style={{ color: '#1a1a2e', fontSize: '0.85rem', fontWeight: 600 }}>Détails techniques</summary>
                  <p style={{ color: '#6b6b7b', fontSize: '0.85rem', lineHeight: 1.8, marginTop: '8px', whiteSpace: 'pre-wrap' }}>
                    {group.solution.technical_details}
                  </p>
                </details>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function DuplicateGroups({ groups }) {
  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '8px', color: '#1a1a2e' }}>
          Groupes de doublons <span style={{ color: '#6b6b7b', fontWeight: 400 }}>({groups.length})</span>
        </h2>
        <p style={{ color: '#6b6b7b' }}>Cliquez sur un groupe pour afficher l'analyse de similarité et la solution proposée.</p>
      </div>
      <div className="list-container">
        {groups.map((group, i) => (
          <GroupCard key={group.group_id} group={group} index={i} />
        ))}
      </div>
    </div>
  );
}
