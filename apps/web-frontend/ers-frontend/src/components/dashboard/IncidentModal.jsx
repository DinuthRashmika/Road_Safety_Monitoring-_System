import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/axiosConfig';
import './IncidentModal.css';
import { useAuth } from '../../hooks/useAuth'; 

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


  if (loading) return <div className="modal-backdrop"><div className="modal-content">Loading...</div></div>;
  if (error) return <div className="modal-backdrop"><div className="modal-content">{error} <button onClick={onClose}>Close</button></div></div>;
  if (!incident) return null;

  const isAdmin = user?.role === 'admin';
  const isNew = incident.status === 'new';
  const isResolved = incident.status === 'resolved';

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>
        <h3>Emergency Details - #{incident.id}</h3>
        
        <div className="modal-body">
          <div className="modal-left">
            <h4>Incident Information</h4>
            <p><strong>Type:</strong> {incident.source === 'traffic' ? 'Traffic Accident' : 'Violence'}</p>
            <p><strong>Score:</strong> {incident.score}</p>
            <p><strong>Reported:</strong> {new Date(incident.reported_at).toLocaleString()}</p>
            <p><strong>Location:</strong> {incident.location.address}</p>
            <h4 className="mt-2">Analysis Results</h4>
            {incident.accident?.fire_present && <p className="analysis-fire">Fire Detected</p>}
            {incident.accident && <p>Vehicles: {incident.accident.vehicles_involved}</p>}
            {incident.violence && <p>Participants: {incident.violence.participants_count}</p>}
            {incident.violence?.weapon_conf > 0 && <p>Weapon Conf: {incident.violence.weapon_conf * 100}%</p>}
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
                <p><strong>Fastest Route: {route.eta_min} min</strong></p>
                <p>Distance: {route.distance_km} km</p>
                <div className="map-placeholder">MAP showing route</div>
              </div>
            ) : (
              <div className="map-placeholder">incident route.</div>
            )}
            <h4 className="mt-2">Scene Image</h4>
            <div className="scene-image-placeholder">
              {incident.media?.image_url ? 
                <img src={incident.media.image_url} alt="Scene" /> :
                'No image provided.'
              }
            </div>
          </div>
        </div>
        
        <div className="modal-footer">
          {isAdmin && (
              <p className="admin-view-status">
                  Status: {isResolved ? 'RESOLVED' : incident.status.toUpperCase()} (View Only)
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