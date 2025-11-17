import React, { useState } from 'react';
import IncidentModal from './IncidentModal';
import './IncidentCard.css';

const IncidentCard = ({ incident }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const {
    id,
    score,
    source,
    location,
    accident,
    violence,
    required_roles = [],
  } = incident;

  let title = source === 'traffic' ? 'Traffic Accident' : 'Violence Incident';
  if (accident?.fire_present) title = 'Multi-Vehicle Accident with Fire';

  const getSeverityClass = (score) => {
    if (score > 90) return 'critical';
    if (score > 75) return 'high';
    if (score > 50) return 'medium';
    return 'low';
  };
  
  const severity = getSeverityClass(score);

  return (
    <>
      <div className={`incident-card ${severity}`}>
        <div className="card-header">
          <span className={`severity-tag ${severity}`}>
            {severity.toUpperCase()} {accident?.fire_present && '- FIRE DETECTED'}
          </span>
          <span className="incident-id">#{id.split('-')[0]}-{id.split('-')[1]}</span>
        </div>
        
        <div className="card-body">
          <div className="card-content">
            <h3>{title}</h3>
            <p>{location.address}</p>
            <div className="card-tags">
              {required_roles.map(role => (
                <span key={role} className={`role-tag ${role}`}>{role}</span>
              ))}
            </div>
          </div>
          <div className="card-actions">
            <div className="score-badge">{Math.round(score)}</div>
            <button className="accept-button" onClick={() => setIsModalOpen(true)}>
              Accept & Respond
            </button>
          </div>
        </div>
      </div>

      {isModalOpen && (
        <IncidentModal 
          incidentId={incident.id} 
          onClose={() => setIsModalOpen(false)} 
        />
      )}
    </>
  );
};

export default IncidentCard;