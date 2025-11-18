import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import api from '../api/axiosConfig';
import './ResponseHistory.css'; 
import { useAuth } from '../hooks/useAuth'; // Import useAuth

const ResponseHistory = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth(); // Get the current user

  // Function to fetch real history data
  const fetchHistory = async () => {
    try {
      setLoading(true);
      // Call the queue endpoint with status="resolved"
      const res = await api.get('/api/incidents/queue', { 
        params: { status: 'resolved' } 
      });
      setHistory(res.data); // Set the real data from the API
    } catch (err) {
      console.error("Failed to fetch history", err);
    } finally {
      setLoading(false);
    }
  };

  // Load history on component mount
  useEffect(() => {
    fetchHistory();
  }, []);

  // Handles the delete button click
  const handleDelete = async (incidentId) => {
    if (!window.confirm("Are you sure you want to permanently delete this incident?")) {
      return;
    }

    try {
      await api.delete(`/api/incidents/${incidentId}`);
      // Refresh the list after successful deletion
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
          {/* This will now be empty because your database is empty */}
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
                {/* Only show delete button if user is admin */}
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