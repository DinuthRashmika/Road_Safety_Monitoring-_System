import React, { useState } from 'react';
import IncidentModal from './IncidentModal';
import './IncidentCard.css';
import { useAuth } from '../../hooks/useAuth'; 

const IncidentCard = ({ incident, onUpdate }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showPending, setShowPending] = useState(false); 
  const { user } = useAuth();
  
  const {
    id,
    score,
    source,
    location,
    accident,
    violence,
    required_roles = [],
    pending_responder_roles = [], 
    reported_at 
  } = incident;

  const formatTime = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleTimeString([], { 
      hour: '2-digit', minute: '2-digit' 
    });
  };

  const getTimeAgo = (dateString) => {
    if (!dateString) return '';
    const diff = new Date() - new Date(dateString);
    const mins = Math.floor(diff / 60000);
    
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return '>1d ago';
  };

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

  const hasPendingResponders = isAdmin && pending_responder_roles.length > 0;

  return (
    <>
      <div className={`incident-card ${severity}`}>
        <div className="card-header">
          <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
             <span className={`severity-tag ${severity}`}>
               {severity?.toUpperCase()} {accident?.fire_present && '- FIRE DETECTED'}
             </span>
             
             {hasPendingResponders && (
               <div 
                 className="pending-alert-icon" 
                 onClick={(e) => {
                    e.stopPropagation();
                    setShowPending(!showPending);
                 }}
                 title="Click to see who hasn't resolved yet"
               >
                 ⚠️ Pending
                 {showPending && (
                   <div className="pending-popup">
                     <strong>Waiting for:</strong>
                     <ul>
                       {pending_responder_roles.map(r => <li key={r}>{r}</li>)}
                     </ul>
                   </div>
                 )}
               </div>
             )}
          </div>
          
          <span className="incident-id">#{id}</span>
        </div>
        
        <div className="card-body">
          <div className="card-content">
            <h3>{title}</h3>
            <p>{location.address}</p>

            <div className="time-row" style={{ fontSize: '0.85rem', color: '#555', marginTop: '6px', marginBottom: '6px', display: 'flex', alignItems: 'center' }}>
                <i className="far fa-clock" style={{ marginRight: '6px' }}></i>
                <span>{formatTime(reported_at)}</span>
                <span style={{ marginLeft: '8px', color: '#d9534f', fontWeight: 'bold', fontSize: '0.8rem' }}>
                    ({getTimeAgo(reported_at)})
                </span>
            </div>

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