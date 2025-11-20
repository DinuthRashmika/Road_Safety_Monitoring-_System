import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import api from '../api/axiosConfig';
import './ResponderList.css'; 
import { useAuth } from '../hooks/useAuth'; 

const ResponderList = () => {
    const [responders, setResponders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null); 
    const { user } = useAuth(); 

    const fetchResponders = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.get('/api/responders'); 
            setResponders(response.data);
        } catch (err) {
            console.error("Error fetching responders:", err);
            setError("Failed to load responder list. Ensure you are logged in as an Admin.");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (responderId, responderName) => {
        if (responderId === user.id) {
             alert("Cannot delete your own active Admin account from this list.");
             return;
        }
        
        if (!window.confirm(`Are you sure you want to permanently delete the responder: ${responderName}? This action cannot be undone.`)) {
            return;
        }
        
        try {
            await api.delete(`/api/responders/${responderId}`);
            fetchResponders(); 
        } catch (err) {
            alert("Failed to delete responder. Check console for details.");
            console.error("Delete failed:", err);
        }
    };
    useEffect(() => {
        if (user?.role === 'admin') {
            fetchResponders(); 
            
            const intervalId = setInterval(() => {
                fetchResponders();
            }, 15000); 
            return () => clearInterval(intervalId);
        }
        setLoading(false);
        
    }, [user]);

    return (
        <Layout>
            <h2>All System Responders</h2>
            <p>View all registered police stations, hospitals, and fire departments in the system.</p>
            
            {error && <div className="error-message">{error}</div>}

            <div className="responder-list-container">
                {loading && responders.length === 0 && <p>Fetching responder data...</p>}
                
                {!loading && responders.length > 0 && responders.map(responder => (
                    <div key={responder.id} className="responder-card">
                        <div className="responder-left">
                            <h4>{responder.name}</h4>
                            <p className="responder-role">{responder.role}</p>
                        </div>
                        <div className="responder-right">
                            <div className="responder-details">
                                <span>{responder.email}</span>
                                <span className="location">{responder.location?.address || 'Location N/A'}</span>
                            </div>
                            {user?.role === 'admin' && (
                                <button 
                                    className="delete-responder-button" 
                                    onClick={() => handleDelete(responder.id, responder.name)}
                                    disabled={responder.id === user.id} 
                                >
                                    Delete
                                </button>
                            )}
                        </div>
                    </div>
                ))}
                
                {!loading && responders.length === 0 && !error && <p>No responders found.</p>}
            </div>
        </Layout>
    );
};

export default ResponderList;