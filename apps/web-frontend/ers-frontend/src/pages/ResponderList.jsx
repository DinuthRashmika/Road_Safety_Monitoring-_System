import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import api from '../api/axiosConfig';
import './ResponderList.css';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

const ResponderEditModal = ({ responder, onClose, onUpdate }) => {
    const [formData, setFormData] = useState({
        name: responder.name,
        email: responder.email,
        role: responder.role,
        address: responder.location?.address || '',
        lat: responder.location?.lat || 0.0,
        lng: responder.location?.lng || 0.0,
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const roles = ['police', 'ambulance', 'fire', 'admin'];

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        const patchData = {
            name: formData.name,
            email: formData.email,
            role: formData.role,
            location: {
                lat: parseFloat(formData.lat),
                lng: parseFloat(formData.lng),
                address: formData.address,
            }
        };

        if (formData.password) {
            patchData.password = formData.password;
        }

        try {
            await api.put(`/api/responders/${responder.id}`, patchData);
            alert('Responder updated successfully!');
            onUpdate();
        } catch (err) {
            console.error("Update failed:", err.response?.data);
            const detail = err.response?.data?.detail || 'Failed to update responder. Check email uniqueness.';
            setError(detail);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <button className="modal-close" onClick={onClose}>×</button>
                <h3>Edit Responder: {responder.name}</h3>

                <form onSubmit={handleSubmit}>
                    {error && <p style={{ color: '#E4080A', marginBottom: '10px' }}>Error: {error}</p>}

                    <div className="form-group">
                        <label>Name</label>
                        <input type="text" name="name" value={formData.name} onChange={handleChange} required />
                    </div>

                    <div className="form-group">
                        <label>Email</label>
                        <input type="email" name="email" value={formData.email} onChange={handleChange} required />
                    </div>

                    <div className="form-group">
                        <label>Role</label>
                        <select name="role" value={formData.role} onChange={handleChange} required>
                            {roles.map(r => <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>)}
                        </select>
                    </div>

                    <h4>Location Details (Station)</h4>
                    <div className="form-group">
                        <label>Address</label>
                        <input type="text" name="address" value={formData.address} onChange={handleChange} />
                    </div>
                    <div className="form-group" style={{ display: 'flex', gap: '10px' }}>
                        <div style={{ flex: 1 }}>
                            <label>Latitude (lat)</label>
                            <input type="number" name="lat" value={formData.lat} onChange={handleChange} step="0.0001" />
                        </div>
                        <div style={{ flex: 1 }}>
                            <label>Longitude (lng)</label>
                            <input type="number" name="lng" value={formData.lng} onChange={handleChange} step="0.0001" />
                        </div>
                    </div>

                    <h4>Change Password (Optional)</h4>
                    <div className="form-group">
                        <label>New Password</label>
                        <input type="password" name="password" value={formData.password} onChange={handleChange} placeholder="Leave blank to keep current password" />
                    </div>

                    <div className="modal-footer" style={{ marginTop: '20px', paddingTop: '10px', borderTop: '1px solid #eee', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                        <button type="button" className="btn-directions" onClick={onClose}>Cancel</button>
                        <button type="submit" className="btn-accept" disabled={loading}>
                            {loading ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

const ResponderList = () => {
    const [responders, setResponders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { user } = useAuth();
    const navigate = useNavigate();

    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [editingResponder, setEditingResponder] = useState(null);

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

    const handleUpdate = () => {
        fetchResponders();
        setIsEditModalOpen(false);
    }

    const handleEdit = (responder) => {
        setEditingResponder(responder);
        setIsEditModalOpen(true);
    }

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
    
    const handleCardClick = (responderId) => {
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

                {!loading && responders.length > 0 && responders
                    .filter(responder => responder.id !== user?.id)
                    .map(responder => (
                        <div
                            key={responder.id}
                            className="responder-card"
                            onClick={() => handleCardClick(responder.id)}
                        >
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
                                    <>
                                        <button
                                            className="edit-responder-button"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleEdit(responder);
                                            }}
                                        >
                                            Edit
                                        </button>
                                        <button
                                            className="delete-responder-button"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDelete(responder.id, responder.name);
                                            }}
                                            disabled={responder.id === user.id}
                                        >
                                            Delete
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>
                    ))}

                {!loading && responders.length === 0 && !error && <p>No responders found.</p>}
            </div>

            {isEditModalOpen && editingResponder && (
                <ResponderEditModal
                    responder={editingResponder}
                    onClose={() => setIsEditModalOpen(false)}
                    onUpdate={handleUpdate}
                />
            )}
        </Layout>
    );
};

export default ResponderList;