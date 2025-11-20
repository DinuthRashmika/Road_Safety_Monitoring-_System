import React, { useState } from 'react';
import IncidentModal from './IncidentModal';
import './IncidentCard.css';
import { useAuth } from '../../hooks/useAuth'; 

const IncidentCard = ({ incident, onUpdate }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { user } = useAuth();
  
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

  const isAdmin = user?.role === 'admin';
  const buttonText = isAdmin ? 'View Details' : 'Accept & Respond';
  const buttonClass = isAdmin ? 'view-details-button' : 'accept-button';

  return (
    <>
      <div className={`incident-card ${severity}`}>
        <div className="card-header">
          <span className={`severity-tag ${severity}`}>
            {severity?.toUpperCase()} {accident?.fire_present && '- FIRE DETECTED'}
          </span>
          <span className="incident-id">#{id}</span>
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
            
            <button className={buttonClass} onClick={() => setIsModalOpen(true)}>
              {buttonText}
            </button>
          </div>
        </div>
      </div>

      {isModalOpen && (
        <IncidentModal 
          incidentId={incident.id} 
          onClose={() => setIsModalOpen(false)} 
          onUpdate={onUpdate}
        />
      )}
    </>
  );
};

export default IncidentCard;