import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import api from '../api/axiosConfig';
import './ResponseHistory.css'; 

const ResponseHistory = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      // NOTE: Your backend doesn't have this endpoint yet.
      // We would need to create a new endpoint like `GET /api/incidents?status=resolved`
      // For now, we will mock the data.
      setHistory([
        { id: 'EMG-045', title: 'Residential Fire', status: 'Resolved' },
        { id: 'EMG-044', title: 'Traffic Accident', status: 'Resolved' },
      ]);
      setLoading(false);
    };
    fetchHistory();
  }, []);

  return (
    <Layout>
      <h2>Response History</h2>
      {loading ? (
        <p>Loading history...</p>
      ) : (
        <div className="history-list">
          {history.map(item => (
            <div key={item.id} className="history-item">
              <div className="history-item-info">
                <h4>{item.id}: {item.title}</h4>
                <p>Completed • Response time: 5:12</p>
              </div>
              <span className="status-resolved">{item.status}</span>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
};

export default ResponseHistory;