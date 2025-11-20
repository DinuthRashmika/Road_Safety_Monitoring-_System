import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import api from '../api/axiosConfig';
import './ResponderList.css'; 

const ResponderList = () => {
    const [responders, setResponders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchResponders = async () => {
        setLoading(true);
        setError(null);
        try {
            // This endpoint is protected, only accessible with an Admin token
            const response = await api.get('/api/responders'); 
            setResponders(response.data);
        } catch (err) {
            console.error("Error fetching responders:", err);
            // 403 Forbidden is expected if a non-admin user somehow accesses this page
            setError("Failed to load responder list. Ensure you are logged in as an Admin.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchResponders();
    }, []);

    return (
        <Layout>
            <h2>All System Responders</h2>
            <p>View all registered police stations, hospitals, and fire departments in the system.</p>
            <button className="refresh-button" onClick={fetchResponders} disabled={loading}>
                {loading ? 'Loading...' : 'Refresh List'}
            </button>
            
            {error && <div className="error-message">{error}</div>}

            <div className="responder-list-container">
                {loading && <p>Fetching responder data...</p>}
                {!loading && responders.length === 0 && <p>No responders found.</p>}

                {!loading && responders.map(responder => (
                    <div key={responder.id} className="responder-card">
                        <div className="responder-info">
                            <h4>{responder.name}</h4>
                            <p className="responder-role">{responder.role}</p>
                        </div>
                        <div className="responder-details">
                            <span>{responder.email}</span>
                            <span className="location">{responder.location?.address || 'Location N/A'}</span>
                        </div>
                    </div>
                ))}
            </div>
        </Layout>
    );
};

export default ResponderList;