import React from 'react';
import Layout from '../components/layout/Layout';

const MapView = () => {
  return (
    <Layout>
      <h2>Map View</h2>
      <div style={{ 
        width: '100%', 
        height: '75vh', 
        background: '#e0e0e0', 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        borderRadius: '8px'
      }}>
        <h3 style={{color: '#888'}}>MAP</h3>
      </div>
    </Layout>
  );
};

export default MapView;