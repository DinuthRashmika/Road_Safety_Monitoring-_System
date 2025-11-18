import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import IncidentCard from '../components/dashboard/IncidentCard';
import TelemetryTile from '../components/dashboard/TelemetryTile';
import api from '../api/axiosConfig';
import './Dashboard.css'; 

const Dashboard = () => {
  const [telemetry, setTelemetry] = useState(null);
  const [queue, setQueue] = useState([]);
  const [loadingQueue, setLoadingQueue] = useState(true);
  const [loadingTelemetry, setLoadingTelemetry] = useState(true);
  const [error, setError] = useState(null);

  const fetchTelemetry = async () => {
    try {
      setLoadingTelemetry(true);
      const res = await api.get('/api/metrics/tiles');
      setTelemetry(res.data);
    } catch (err) {
      console.error('Failed to fetch telemetry', err);
      setError('Failed to load dashboard stats.');
    } finally {
      setLoadingTelemetry(false);
    }
  };

  const fetchQueue = async () => {
    try {
      setLoadingQueue(true);

      const res = await api.get('/api/incidents/queue', {
        params: { status: 'active' }
      });
      setQueue(res.data);
    } catch (err) {
      console.error('Failed to fetch queue', err);
      setError('Failed to load incident queue.');
    } finally {
      setLoadingQueue(false);
    }
  };

  const handleIncidentUpdate = () => {
    fetchTelemetry();
    fetchQueue();
  };

  useEffect(() => {
    handleIncidentUpdate(); 
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    
    const intervalId = setInterval(() => {
      console.log('Auto-refreshing data...');
      handleIncidentUpdate();
    }, 10000); // Refresh every 10 seconds

    
    return () => clearInterval(intervalId);
  }, []); 

  return (
    <Layout>
      <div className="dashboard-header">
        <h2>Emergency Response Dashboard</h2>
        <p>Monitor and respond to active emergencies in your area</p>
      </div>

      <div className="telemetry-grid">
        {loadingTelemetry ? <p>Loading stats...</p> : telemetry && (
          <>
            <TelemetryTile title="Active Emergencies" value={telemetry.active} />
            <TelemetryTile title="Resolved Today" value={telemetry.resolved_window} />
          </>
        )}
      </div>

      <div className="queue-header">
        <h3>Priority Emergency Queue</h3>
      </div>

      {error && <div className="error-message">{error}</div>}
      
      <div className="incident-queue">
        {loadingQueue && <p>Loading queue...</p>}
        {!loadingQueue && queue.length === 0 && <p>No active emergencies in your area.</p>}
        
        {queue.map(incident => (
          <IncidentCard 
            key={incident.id} 
            incident={incident} 
            onUpdate={handleIncidentUpdate}
          />
        ))}
      </div>
    </Layout>
  );
};

export default Dashboard;