import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import api from '../api/axiosConfig';
import IncidentModal from '../components/dashboard/IncidentModal';
import './ResponseHistory.css';

const ResponseHistory = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedIncidentId, setSelectedIncidentId] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const res = await api.get('/api/incidents/queue', {
        params: { status: 'resolved' }
      });
      setHistory(res.data);
    } catch (err) {
      console.error('Failed to fetch history', err);
      setError('Failed to load response history.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ', ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <Layout>
      <div className="history-header">
        <h2>Response History</h2>
        <p>Review resolved incidents and response performance</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="history-container">
        {loading ? (
          <div className="loading-state">Loading history...</div>
        ) : history.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">📋</span>
            <p>No resolved incidents found</p>
          </div>
        ) : (
          <table className="history-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Location</th>
                <th>Resolved At</th>
                <th>Score</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {history.map((incident) => (
                <tr key={incident.id}>
                  <td className="incident-id">#{incident.id.slice(-6).toUpperCase()}</td>
                  <td className="incident-location">{incident.location.address}</td>
                  <td className="incident-time">{formatDate(incident.reported_at)}</td>
                  <td>
                    <span className={`score-badge ${incident.score >= 85 ? 'critical' : incident.score >= 70 ? 'high' : incident.score >= 50 ? 'medium' : 'low'}`}>
                      {incident.score}
                    </span>
                  </td>
                  <td>
                    <button 
                      className="view-details-btn" 
                      onClick={() => setSelectedIncidentId(incident.id)}
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selectedIncidentId && (
        <IncidentModal 
          incidentId={selectedIncidentId} 
          onClose={() => setSelectedIncidentId(null)}
          onUpdate={fetchHistory}
        />
      )}
    </Layout>
  );
};

export default ResponseHistory;