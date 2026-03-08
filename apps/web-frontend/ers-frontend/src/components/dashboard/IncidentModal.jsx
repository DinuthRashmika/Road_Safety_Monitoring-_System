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

// Helper function to check if URL is local API endpoint
const isLocalApiUrl = (url) => {
  return url && (url.startsWith('/api/images/') || !url.startsWith('http'));
};

// Helper function to convert Shenal's Windows paths to proper URLs
const getImageUrl = (rawPath, baseUrl) => {
  if (!rawPath) return null;
  
  // If it's already a full URL, return as is
  if (rawPath.startsWith('http')) return rawPath;
  
  // If it's already a proper API path, just add base URL
  if (rawPath.startsWith('/api/images/')) {
    return `${baseUrl}${rawPath}`;
  }
  
  // Clean Windows paths: replace backslashes with forward slashes
  const cleanPath = rawPath.replace(/\\/g, '/');
  
  // URL encode each segment to handle spaces and special characters
  const encodedSegments = cleanPath.split('/').map(segment => 
    encodeURIComponent(segment)
  ).join('/');
  
  // Construct the final URL
  return `${baseUrl}/api/images/${encodedSegments}`;
};

const IncidentModal = ({ incidentId, onClose, onUpdate }) => {
  const [incident, setIncident] = useState(null);
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [imageLoading, setImageLoading] = useState(true);
  
  const navigate = useNavigate();
  const { user } = useAuth(); 

  // Backend base URL to resolve local images
  const API_BASE_URL = "http://localhost:8000";

  useEffect(() => {
    fetchDetails();
  }, [incidentId]);

  const fetchDetails = async () => {
    try {
      setLoading(true);
      console.log(`Fetching incident details for ID: ${incidentId}`);
      const incidentRes = await api.get(`/api/incidents/${incidentId}`);
      console.log("Incident data received:", incidentRes.data);
      setIncident(incidentRes.data);
      
      if (incidentRes.data.status !== 'new' && incidentRes.data.status !== 'unverified') {
        fetchRoute(incidentId);
      }
    } catch (err) {
      console.error('Failed to fetch incident details:', err);
      setError('Failed to load incident details.');
    } finally {
      setLoading(false);
    }
  };

  const fetchRoute = async (id) => {
    try {
      console.log(`Fetching route for incident: ${id}`);
      const routeRes = await api.get(`/api/incidents/${id}/route`);
      setRoute(routeRes.data); 
    } catch (err) {
      console.error('Failed to fetch route', err);
    }
  };

  const handleAccept = async () => {
    if (user?.role === 'admin') return; 
    
    setIsUpdating(true);
    try {
      await api.post(`/api/incidents/${incidentId}/accept`);
      await fetchDetails(); 
      alert('Incident accepted. You are now assigned.');
      if (typeof onUpdate === 'function') {
        onUpdate(); 
      }
    } catch (err) {
      alert(`Failed to accept incident: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleStartRoute = async () => {
    if (!route) {
        alert("Route is still calculating. Please wait a moment.");
        return;
    }

    setIsUpdating(true);
    try {
        await api.post(`/api/incidents/${incidentId}/status`, { status: 'enroute' });
        if (typeof onUpdate === 'function') onUpdate();

        const updatedIncident = { ...incident, status: 'enroute' };
        navigate('/map-view', { state: { incident: updatedIncident, route } });

    } catch (err) {
        alert(`Failed to start route: ${err.response?.data?.detail || err.message}`);
        setIsUpdating(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    setIsUpdating(true);
    try {
        await api.post(`/api/incidents/${incidentId}/status`, { status: newStatus });
        await fetchDetails(); 
        if (typeof onUpdate === 'function') onUpdate();
    } catch (err) {
        alert(`Failed to update status: ${err.response?.data?.detail || err.message}`);
    } finally {
        setIsUpdating(false);
    }
  };
  
  const handleGetDirections = () => {
    if (!route) {
      alert("Route data is not available yet. Please wait a moment and try again.");
      return;
    }
    navigate('/map-view', { state: { incident, route } });
  };

  const getRoleStatusList = () => {
    if (!incident) return [];
    
    const roles = incident.required_roles || [];
    
    return roles.map(role => {
        const assigned = incident.assigned_responders?.find(r => r.role === role);
        if (assigned) {
            return {
                ...assigned,
                isAssigned: true
            };
        } else {
            return {
                role: role,
                name: 'Waiting for Responder...',
                status: 'pending',
                isAssigned: false
            };
        }
    });
  };

  const handleResponderClick = (responder) => {
      if (isAdmin && responder.id) {
          navigate(`/profile/${responder.id}`);
      }
  };

  const formatDate = (d) => d ? new Date(d).toLocaleDateString(undefined, { weekday:'short', year:'numeric', month:'short', day:'numeric' }) : 'N/A';
  const formatTime = (d) => d ? new Date(d).toLocaleTimeString(undefined, { hour:'2-digit', minute:'2-digit' }) : 'N/A';
  
  const getTimeAgo = (d) => {
      if(!d) return '';
      const m = Math.floor((new Date() - new Date(d))/60000);
      if(m<1) return '(Just now)';
      if(m<60) return `(${m} mins ago)`;
      const h = Math.floor(m/60);
      return h<24 ? `(${h} hours ago)` : `(${Math.floor(h/24)} days ago)`;
  };

  const handleImageError = () => {
    console.error("Image failed to load:", imageUrl);
    setImageError(true);
    setImageLoading(false);
  };

  const handleImageLoad = () => {
    console.log("Image loaded successfully:", imageUrl);
    setImageLoading(false);
  };

  if (loading) return (
    <div className="modal-backdrop">
      <div className="modal-content">
        <div className="loading-spinner">Loading incident details...</div>
      </div>
    </div>
  );
  
  if (error) return (
    <div className="modal-backdrop">
      <div className="modal-content">
        <p className="error-message">{error}</p>
        <button onClick={onClose} className="btn-close">Close</button>
      </div>
    </div>
  );
  
  if (!incident) return null;

  const isAdmin = user?.role === 'admin';
  const isNew = incident.status === 'new';
  const myStatus = incident.status; 

  // Get image URL only for traffic incidents
  const rawImageUrl = incident.media?.image_url;
  const imageUrl = getImageUrl(rawImageUrl, API_BASE_URL);

  const driveId = getDriveId(rawImageUrl);
  const isLocalImage = isLocalApiUrl(rawImageUrl);
  const roleStatusList = getRoleStatusList();

  // Determine if this is a violence/human behavior incident
  const isViolence = incident.source === 'violence' || incident.source === 'human_behavior';
  const isTraffic = incident.source === 'traffic';

  // Debug log
  console.log("Incident ID:", incidentId);
  console.log("Source:", incident.source);
  console.log("Is Violence:", isViolence);
  console.log("Raw URL from API:", rawImageUrl);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>
        <h3>Emergency Details - #{incident.id ? incident.id.slice(-6) : '...'}</h3>
        
        <div className="modal-body">
          {/* LEFT COLUMN - Always visible */}
          <div className="modal-left">
            <h4>Incident Information</h4>
            <p><strong>Type:</strong> {incident.source === 'traffic' ? 'Traffic Accident' : 'Violence'}</p>
            <p><strong>Score:</strong> <span className="score-badge">{incident.score}</span></p>
            
            <div className="time-display-group">
                <p className="time-row"><strong>Date:</strong> {formatDate(incident.reported_at)}</p>
                <p className="time-row">
                    <strong>Time:</strong> {formatTime(incident.reported_at)} 
                    <span className="time-ago-text">
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
            {incident.violence?.threat_score && <p>Threat Score: {(incident.violence.threat_score * 100).toFixed(1)}%</p>}
            {incident.violence?.action && <p>Action: {incident.violence.action}</p>}
            <p>Severity: {incident.severity_grade}</p>
            
            <h4 className="mt-2">Required Responders</h4>
            <div className="role-tags-modal">
              {incident.required_roles.map(role => (
                <span key={role} className={`role-tag ${role}`}>{role}</span>
              ))}
            </div>
          </div>

          {/* RIGHT COLUMN - Conditional based on incident type */}
          {isTraffic && (
            /* TRAFFIC INCIDENT - Show Scene Evidence with image */
            <div className="modal-right">
              <h4>Scene Evidence</h4>
              <div className="scene-image-placeholder">
                {imageUrl ? (
                  driveId ? (
                    <iframe 
                        src={`https://drive.google.com/file/d/${driveId}/preview`}
                        width="100%" 
                        height="250px" 
                        className="evidence-iframe"
                        title="Scene Evidence"
                        allowFullScreen
                        onLoad={() => console.log("Google Drive iframe loaded")}
                        onError={() => console.error("Google Drive iframe failed")}
                    />
                  ) : (
                    <>
                      {imageLoading && <div className="image-loading">Loading image...</div>}
                      <img 
                          src={imageUrl} 
                          alt="Scene" 
                          className="evidence-image"
                          style={{ display: imageError ? 'none' : 'block' }}
                          onLoad={handleImageLoad}
                          onError={handleImageError}
                      />
                      {imageError && (
                        <div className="image-error-container">
                          <span className="image-load-error">⚠️ Image failed to load</span>
                          {isLocalImage && (
                            <div className="image-debug-info">
                              <p>Debug info:</p>
                              <p>Raw path: {rawImageUrl}</p>
                              <p>Final URL: {imageUrl}</p>
                              <p>Try accessing directly:</p>
                              <a href={imageUrl} target="_blank" rel="noopener noreferrer">
                                Open image directly
                              </a>
                            </div>
                          )}
                        </div>
                      )}
                    </>
                  )
                ) : (
                  <span className="no-image-text">No image provided</span>
                )}
              </div>
              {imageUrl && !imageError && (
                  <div className="view-original-container">
                      <a href={imageUrl} target="_blank" rel="noopener noreferrer" className="view-original-link">
                          View Original ↗
                      </a>
                  </div>
              )}
            </div>
          )}

          {isViolence && (
            /* VIOLENCE INCIDENT - Show detailed violence information instead of image */
            <div className="modal-right">
              <h4>Violence Details</h4>
              <div className="violence-details-box">
                {incident.violence?.threat_level && (
                  <p><strong>Threat Level:</strong> 
                    <span className={`threat-badge ${incident.violence.threat_level.toLowerCase()}`}>
                      {incident.violence.threat_level}
                    </span>
                  </p>
                )}
                
                {incident.violence?.threat_score && (
                  <p><strong>Threat Score:</strong> {(incident.violence.threat_score * 100).toFixed(1)}%</p>
                )}
                
                {incident.violence?.action && (
                  <p><strong>Action:</strong> {incident.violence.action}</p>
                )}
                
                {incident.violence?.action_confidence && (
                  <p><strong>Action Confidence:</strong> {(incident.violence.action_confidence * 100).toFixed(1)}%</p>
                )}
                
                {incident.violence?.has_weapon && (
                  <p><strong>Weapon Detected:</strong> Yes</p>
                )}
                
                {incident.violence?.weapon_conf > 0 && (
                  <p><strong>Weapon Confidence:</strong> {(incident.violence.weapon_conf * 100).toFixed(1)}%</p>
                )}
                
                {incident.violence?.sustained_seconds > 0 && (
                  <p><strong>Duration:</strong> {incident.violence.sustained_seconds} seconds</p>
                )}
                
                {incident.violence?.objects_detected && incident.violence.objects_detected.length > 0 && (
                  <div className="objects-detected">
                    <p><strong>Objects Detected:</strong></p>
                    <ul>
                      {incident.violence.objects_detected.map((obj, idx) => (
                        <li key={idx}>
                          {obj.object} ({(obj.confidence * 100).toFixed(1)}% confidence)
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {incident.violence?.human_summary && (
                  <div className="human-summary">
                    <p><strong>Summary:</strong></p>
                    <p>{incident.violence.human_summary}</p>
                  </div>
                )}
                
                {incident.violence?.reasoning && (
                  <div className="reasoning">
                    <p><strong>Reasoning:</strong></p>
                    <p>{incident.violence.reasoning}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
        
        <div className="modal-footer">
          {isAdmin && (
              <p className="admin-view-status" style={{color:'#777', fontStyle:'italic'}}>
                  Monitoring Incident Status
              </p>
          )}

          {!isAdmin && (
             <>
                {myStatus === 'new' && (
                    <button className="btn-accept" onClick={handleAccept} disabled={isUpdating}>
                        {isUpdating ? 'Accepting...' : 'Accept Emergency & Dispatch'}
                    </button>
                )}

                {myStatus === 'accepted' && (
                    <button className="btn-action enroute" onClick={handleStartRoute} disabled={isUpdating}>
                        {isUpdating ? 'Starting...' : 'Start Route ➜'}
                    </button>
                )}

                {myStatus === 'enroute' && (
                    <>
                        <button className="btn-directions" onClick={handleGetDirections}>View Map</button>
                        <button className="btn-action arrived" onClick={() => handleStatusChange('arrived')} disabled={isUpdating}>
                            I Have Arrived 📍
                        </button>
                    </>
                )}

                {myStatus === 'arrived' && (
                    <button className="btn-action resolve" onClick={() => handleStatusChange('resolved')} disabled={isUpdating}>
                        ✅ Mark Resolved
                    </button>
                )}

                {myStatus === 'resolved' && (
                    <span style={{color: '#5cb85c', fontWeight: 'bold', fontSize: '1rem'}}>
                        Incident Resolved
                    </span>
                )}
             </>
          )}
        </div>
      </div>
    </div>
  );
};

export default IncidentModal;