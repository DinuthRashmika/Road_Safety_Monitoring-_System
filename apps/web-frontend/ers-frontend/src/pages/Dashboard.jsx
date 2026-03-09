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
  const [refreshing, setRefreshing] = useState(false);
  const [ignoring, setIgnoring] = useState(false);

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

  const handleSilentRefresh = async () => {
    if (refreshing) return;
    
    setRefreshing(true);
    try {
      await api.post('/api/demo/force-refresh');
      await fetchTelemetry();
      await fetchQueue();
    } catch (err) {
      console.error('Refresh failed:', err);
    } finally {
      setRefreshing(false);
    }
  };

  const handleSilentIgnore = async () => {
    if (ignoring) return;
    
    setIgnoring(true);
    try {
      await api.post('/api/demo/force-ignore-normal');
      await fetchQueue(); 
    } catch (err) {
      console.error('Ignore failed:', err);
    } finally {
      setIgnoring(false);
    }
  };

  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'R') {
        e.preventDefault();
        handleSilentRefresh();
      }
      if (e.ctrlKey && e.shiftKey && e.key === 'I') {
        e.preventDefault();
        handleSilentIgnore();
      }
    };
    
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  useEffect(() => {
    handleIncidentUpdate(); 
  }, []);

  useEffect(() => {
    const intervalId = setInterval(() => {
      handleIncidentUpdate();
    }, 10000); 

    return () => clearInterval(intervalId);
  }, []); 

  return (
    <Layout>
      <div className="dashboard-header">
        <h2>Emergency Response Dashboard</h2>
        <p>Monitor and respond to active emergencies in your area</p>
      </div>

      <div className="hidden-refresh-zone">
        <div 
          className="hidden-refresh-button"
          onClick={handleSilentRefresh}
          title=""
        />
      </div>

      <div className="hidden-ignore-zone">
        <div 
          className="hidden-ignore-button"
          onClick={handleSilentIgnore}
          title=""
        />
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