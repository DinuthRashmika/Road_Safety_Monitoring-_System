import React, { useState, useEffect } from 'react';
import api from '../../api/axiosConfig';
import './IncidentModal.css';

const IncidentModal = ({ incidentId, onClose }) => {
  const [incident, setIncident] = useState(null);
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isAccepting, setIsAccepting] = useState(false);

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        setLoading(true);
        const incidentRes = await api.get(`/api/incidents/${incidentId}`);
        setIncident(incidentRes.data);
        
        // If incident is already accepted, fetch its route
        if (incidentRes.data.status !== 'new') {
          fetchRoute();
        }
      } catch (err) {
        setError('Failed to load incident details.');
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [incidentId]);

  const fetchRoute = async () => {
    try {
      const routeRes = await api.get(`/api/incidents/${incidentId}/route`);
      setRoute(routeRes.data);
    } catch (err) {
      console.error('Failed to fetch route', err);
    }
  };

  const handleAccept = async () => {
    setIsAccepting(true);
    try {
      await api.post(`/api/incidents/${incidentId}/accept`);
      
      // Refresh details and fetch route
      const incidentRes = await api.get(`/api/incidents/${incidentId}`);
      setIncident(incidentRes.data);
      fetchRoute();
      alert('Incident accepted. You are now assigned.');
    } catch (err) {
      alert('Failed to accept incident.');
    } finally {
      setIsAccepting(false);
    }
  };

  if (loading) return <div className="modal-backdrop"><div className="modal-content">Loading...</div></div>;
  if (error) return <div className="modal-backdrop"><div className="modal-content">{error} <button onClick={onClose}>Close</button></div></div>;
  if (!incident) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>
        <h3>Emergency Details - #{incident.id.split('-')[1]}</h3>
        
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
              <div className="map-placeholder">Accept incident to see route.</div>
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
          {incident.status === 'new' && (
            <button className="btn-accept" onClick={handleAccept} disabled={isAccepting}>
              {isAccepting ? 'Accepting...' : 'Accept Emergency & Dispatch'}
            </button>
          )}
          {incident.status !== 'new' && (
             <button className="btn-directions">Get Directions</button>
          )}
        </div>
      </div>
    </div>
  );
};

export default IncidentModal;