import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/axiosConfig';
import './IncidentModal.css';
import { useAuth } from '../../hooks/useAuth'; 

const getDriveId = (url) => {
  if (!url || !url.includes('drive.google.com')) return null;
  
  const pathMatch = url.match(/\/d\/([^/]+)/);
  if (pathMatch) return pathMatch[1];

  const queryMatch = url.match(/id=([^&]+)/);
  if (queryMatch) return queryMatch[1];

  return null;
};

const IncidentModal = ({ incidentId, onClose, onUpdate }) => {
  const [incident, setIncident] = useState(null);
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isAccepting, setIsAccepting] = useState(false);
  
  const navigate = useNavigate();
  const { user } = useAuth(); 

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        setLoading(true);
        const incidentRes = await api.get(`/api/incidents/${incidentId}`);
        setIncident(incidentRes.data);
        
        if (incidentRes.data.status !== 'new') {
          fetchRoute(incidentId);
        }
      } catch (err) {
        setError('Failed to load incident details.');
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [incidentId]);

  const fetchRoute = async (id) => {
    try {
      const routeRes = await api.get(`/api/incidents/${id}/route`);
      setRoute(routeRes.data); 
    } catch (err) {
      console.error('Failed to fetch route', err);
    }
  };

  const handleAccept = async () => {
    if (user?.role === 'admin') return; 
    
    setIsAccepting(true);
    try {
      const response = await api.post(`/api/incidents/${incidentId}/accept`);
      setIncident(response.data); 
      await fetchRoute(incidentId); 
      alert('Incident accepted. You are now assigned.');
      if (typeof onUpdate === 'function') {
        onUpdate(); 
      }
    } catch (err) {
      alert(`Failed to accept incident: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsAccepting(false);
    }
  };
  
  const handleGetDirections = () => {
    if (!route) {
      alert("Route data is not available yet. Please wait a moment and try again.");
      return;
    }
    navigate('/map-view', { state: { incident, route } });
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString(undefined, { 
      weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' 
    });
  };

  const formatTime = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleTimeString(undefined, { 
      hour: '2-digit', minute: '2-digit' 
    });
  };

  const getTimeAgo = (dateString) => {
    if (!dateString) return '';
    const diff = new Date() - new Date(dateString);
    const mins = Math.floor(diff / 60000);
    
    if (mins < 1) return '(Just now)';
    if (mins < 60) return `(${mins} mins ago)`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `(${hours} hours ago)`;
    return '';
  };

  if (loading) return <div className="modal-backdrop"><div className="modal-content">Loading...</div></div>;
  if (error) return <div className="modal-backdrop"><div className="modal-content">{error} <button onClick={onClose}>Close</button></div></div>;
  if (!incident) return null;

  const isAdmin = user?.role === 'admin';
  const isNew = incident.status === 'new';
  const isResolved = incident.status === 'resolved';

  const imageUrl = incident.media?.image_url;
  const driveId = getDriveId(imageUrl);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>
        <h3>Emergency Details - #{incident.id ? incident.id.slice(-6) : '...'}</h3>
        
        <div className="modal-body">
          <div className="modal-left">
            <h4>Incident Information</h4>
            <p><strong>Type:</strong> {incident.source === 'traffic' ? 'Traffic Accident' : 'Violence'}</p>
            <p><strong>Score:</strong> <span className="score-badge">{incident.score}</span></p>
            
            <div className="time-display-group" style={{ marginBottom: '10px', padding: '5px', background: '#f8f9fa', borderRadius: '4px' }}>
                <p style={{ margin: '2px 0' }}><strong>Date:</strong> {formatDate(incident.reported_at)}</p>
                <p style={{ margin: '2px 0' }}>
                    <strong>Time:</strong> {formatTime(incident.reported_at)} 
                    <span style={{ color: '#d9534f', marginLeft: '8px', fontWeight: 'bold' }}>
                        {getTimeAgo(incident.reported_at)}
                    </span>
                </p>
            </div>

            <p><strong>Location:</strong> {incident.location.address}</p>
            
            <h4 className="mt-2">Analysis Results</h4>
            {incident.accident?.fire_present && <p className="analysis-fire">🔥 Fire Detected</p>}
            {incident.accident && <p>Vehicles Involved: {incident.accident.vehicles_involved}</p>}
            {incident.violence && <p>Participants: {incident.violence.participants_count}</p>}
            {incident.violence?.weapon_conf > 0 && <p>Weapon Conf: {(incident.violence.weapon_conf * 100).toFixed(1)}%</p>}
            <p>Severity: {incident.severity_grade}</p>
            
            <h4 className="mt-2">Required Responders</h4>
            <div className="role-tags-modal">
              {incident.required_roles.map(role => (
                <span key={role} className={`role-tag ${role}`}>{role}</span>
              ))}
            </div>
          </div>

          <div className="modal-right">
            <h4>Location & Route</h4>
            {route ? (
              <div className="route-info">
                <p><strong>Distance:</strong> {route.distance_km} km</p>
                <div className="map-placeholder">
                   Route Loaded<br/>(Click 'Get Directions' to view)
                </div>
              </div>
            ) : (
              <div className="map-placeholder">
                  {isNew ? 'Accept to calculate route' : 'Calculating route...'}
              </div>
            )}
            
            <h4 className="mt-2">Scene Evidence</h4>
            <div className="scene-image-placeholder" style={{ 
                minHeight: '200px', 
                backgroundColor: '#f5f5f5', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                overflow: 'hidden',
                borderRadius: '4px'
            }}>
              {imageUrl ? (
                driveId ? (
                   <iframe 
                       src={`https://drive.google.com/file/d/${driveId}/preview`}
                       width="100%" 
                       height="250px" 
                       style={{ border: 'none' }}
                       title="Scene Evidence"
                       allowFullScreen
                   />
                ) : (
                   <img 
                       src={imageUrl} 
                       alt="Scene" 
                       style={{ maxWidth: '100%', maxHeight: '250px', objectFit: 'contain' }}
                       onError={(e) => {
                           e.target.style.display='none';
                           e.target.parentNode.innerHTML = `<span style="color:#666; font-size:0.8rem">Image failed to load.</span>`;
                       }}
                   />
                )
              ) : (
                <span style={{color: '#888'}}>No image provided</span>
              )}
            </div>
            {imageUrl && (
                <div style={{ textAlign: 'right', marginTop: '5px' }}>
                    <a href={imageUrl} target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.85rem', color: '#007bff' }}>
                        View Original ↗
                    </a>
                </div>
            )}
          </div>
        </div>
        
        <div className="modal-footer">
          {isAdmin && (
              <p className="admin-view-status">
              </p>
          )}
          {!isAdmin && isNew && (
            <button className="btn-accept" onClick={handleAccept} disabled={isAccepting}>
              {isAccepting ? 'Accepting...' : 'Accept Emergency & Dispatch'}
            </button>
          )}
          
          {!isAdmin && !isNew && !isResolved && (
             <button className="btn-directions" onClick={handleGetDirections} disabled={!route}>
                {route ? 'Get Directions' : 'Loading Route...'}
             </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default IncidentModal;