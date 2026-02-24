import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import api from '../api/axiosConfig';
import './ResponseHistory.css'; 
import { useAuth } from '../hooks/useAuth'; 

const ResponseHistory = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth(); 

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const res = await api.get('/api/incidents/queue', { 
        params: { status: 'resolved' } 
      });
      setHistory(res.data);
    } catch (err) {
      console.error("Failed to fetch history", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleDelete = async (incidentId) => {
    if (!window.confirm("Are you sure you want to permanently delete this incident?")) {
      return;
    }

    try {
      await api.delete(`/api/incidents/${incidentId}`);
      fetchHistory();
    } catch (err) {
      alert("Failed to delete incident. You must be an Admin to do this.");
      console.error("Failed to delete", err);
    }
  };

  return (
    <Layout>
      <h2>Response History</h2>
      {loading ? (
        <p>Loading history...</p>
      ) : (
        <div className="history-list">
          {history.length === 0 && <p>No resolved incidents found.</p>}
          
          {history.map(item => (
            <div key={item.id} className="history-item">
              <div className="history-item-info">
                <h4>{item.source === 'traffic' ? 'Traffic Accident' : 'Violence Incident'}</h4>
                <p>#{item.id}</p>
                <p>{item.location?.address || 'No address'}</p>
              </div>
              
              <div className="history-item-actions">
                <span className="status-resolved">Resolved</span>
                {user && user.role === 'admin' && (
                  <button 
                    className="delete-button" 
                    onClick={() => handleDelete(item.id)}
                  >
                    Delete
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
};

export default ResponseHistory;