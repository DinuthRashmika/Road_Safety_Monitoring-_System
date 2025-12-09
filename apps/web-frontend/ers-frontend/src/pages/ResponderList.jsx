import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import api from '../api/axiosConfig';
import './ResponderList.css';
import { useAuth } from '../hooks/useAuth';

// --- CREATE MODAL COMPONENT ---
const ResponderCreateModal = ({ onClose, onCreate }) => {
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        password: '',
        role: 'police',
        address: '',
        lat: '',
        lng: '',
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

        // Construct payload matching backend schema
        const payload = {
            name: formData.name,
            email: formData.email,
            password: formData.password,
            role: formData.role,
            location: {
                address: formData.address,
                lat: parseFloat(formData.lat) || 0,
                lng: parseFloat(formData.lng) || 0
            }
        };

        try {
            await api.post('/api/responders/', payload);
            alert('Responder created successfully!');
            onCreate(); // Trigger refresh in parent
        } catch (err) {
            console.error("Create failed:", err.response?.data);
            setError(err.response?.data?.detail || 'Failed to create responder.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <button className="modal-close" onClick={onClose}>×</button>
                <div className="modal-header-title">
                   <h3>Add New Responder</h3>
                </div>

                <form onSubmit={handleSubmit}>
                    {error && <div className="error-message">{error}</div>}

                    <div className="form-section">
                        <h4>Account Details</h4>
                        <div className="form-group-grid">
                            <div className="form-group">
                                <label>Name / Station Name</label>
                                <input type="text" name="name" value={formData.name} onChange={handleChange} placeholder="e.g. Central Police" required />
                            </div>
                            <div className="form-group">
                                <label>Role</label>
                                <select name="role" value={formData.role} onChange={handleChange} required>
                                    {roles.map(r => <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>)}
                                </select>
                            </div>
                        </div>
                        <div className="form-group-grid">
                             <div className="form-group">
                                <label>Email</label>
                                <input type="email" name="email" value={formData.email} onChange={handleChange} placeholder="user@system.com" required />
                            </div>
                            <div className="form-group">
                                <label>Password</label>
                                <input type="password" name="password" value={formData.password} onChange={handleChange} placeholder="******" required minLength="6" />
                            </div>
                        </div>
                    </div>

                    <div className="form-section">
                        <h4>Location (Base Station)</h4>
                        <div className="form-group">
                            <label>Address</label>
                            <input type="text" name="address" value={formData.address} onChange={handleChange} placeholder="e.g. 123 Main St" />
                        </div>
                        <div className="form-group-grid">
                            <div className="form-group">
                                <label>Latitude</label>
                                <input type="number" name="lat" value={formData.lat} onChange={handleChange} step="0.000001" placeholder="0.00" />
                            </div>
                            <div className="form-group">
                                <label>Longitude</label>
                                <input type="number" name="lng" value={formData.lng} onChange={handleChange} step="0.000001" placeholder="0.00" />
                            </div>
                        </div>
                    </div>

                    <div className="modal-footer">
                        <button type="button" className="btn-directions" onClick={onClose}>Cancel</button>
                        <button type="submit" className="btn-accept" disabled={loading}>
                            {loading ? 'Creating...' : 'Create Responder'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

// --- EDIT MODAL COMPONENT (Existing) ---
const ResponderEditModal = ({ responder, onClose, onUpdate }) => {
    const [formData, setFormData] = useState({
        name: responder.name,
        email: responder.email,
        role: responder.role,
        address: responder.location?.address || '',
        lat: responder.location?.lat || 0.0,
        lng: responder.location?.lng || 0.0,
        password: '' // Optional for edit
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
            const detail = err.response?.data?.detail || 'Failed to update responder.';
            setError(detail);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <button className="modal-close" onClick={onClose}>×</button>
                <div className="modal-header-title">
                    <h3>Edit Responder: {responder.name}</h3>
                </div>

                <form onSubmit={handleSubmit}>
                    {error && <div className="error-message">{error}</div>}

                    <div className="form-section">
                        <h4>Account Details</h4>
                        <div className="form-group-grid">
                             <div className="form-group">
                                <label>Name</label>
                                <input type="text" name="name" value={formData.name} onChange={handleChange} required />
                            </div>
                            <div className="form-group">
                                <label>Role</label>
                                <select name="role" value={formData.role} onChange={handleChange} required>
                                    {roles.map(r => <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>)}
                                </select>
                            </div>
                        </div>
                        <div className="form-group">
                            <label>Email</label>
                            <input type="email" name="email" value={formData.email} onChange={handleChange} required />
                        </div>
                    </div>

                    <div className="form-section">
                        <h4>Location Details</h4>
                        <div className="form-group">
                            <label>Address</label>
                            <input type="text" name="address" value={formData.address} onChange={handleChange} />
                        </div>
                        <div className="form-group-grid">
                            <div className="form-group">
                                <label>Latitude</label>
                                <input type="number" name="lat" value={formData.lat} onChange={handleChange} step="0.000001" />
                            </div>
                            <div className="form-group">
                                <label>Longitude</label>
                                <input type="number" name="lng" value={formData.lng} onChange={handleChange} step="0.000001" />
                            </div>
                        </div>
                    </div>

                    <div className="form-section">
                        <h4>Change Password <small>(Optional)</small></h4>
                        <div className="form-group">
                            <input type="password" name="password" value={formData.password} onChange={handleChange} placeholder="New password (leave blank to keep current)" />
                        </div>
                    </div>

                    <div className="modal-footer">
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

// --- MAIN PAGE COMPONENT ---
const ResponderList = () => {
    const [responders, setResponders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { user } = useAuth();

    // Modal States
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [editingResponder, setEditingResponder] = useState(null);
    
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

    const fetchResponders = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.get('/api/responders');
            setResponders(response.data);
        } catch (err) {
            console.error("Error fetching responders:", err);
            setError("Failed to load responder list.");
        } finally {
            setLoading(false);
        }
    };

    const handleCreateSuccess = () => {
        setIsCreateModalOpen(false);
        fetchResponders();
    }

    const handleUpdateSuccess = () => {
        setIsEditModalOpen(false);
        setEditingResponder(null);
        fetchResponders();
    }

    const handleEdit = (responder) => {
        setEditingResponder(responder);
        setIsEditModalOpen(true);
    }

    const handleDelete = async (responderId, responderName) => {
        if (responderId === user.id) {
            alert("Cannot delete your own active Admin account.");
            return;
        }
        
        if (!window.confirm(`Are you sure you want to delete ${responderName}?`)) {
            return;
        }
        
        try {
            await api.delete(`/api/responders/${responderId}`);
            fetchResponders();
        } catch (err) {
            alert("Failed to delete responder.");
        }
    };

    useEffect(() => {
        if (user?.role === 'admin') {
            fetchResponders();
        } else {
            setLoading(false); // Not admin, stop loading
        }
    }, [user]);

    return (
        <Layout>
            <div className="page-header-flex">
                <div>
                    <h2>All System Responders</h2>
                    <p>Manage police stations, hospitals, and fire departments.</p>
                </div>
                {/* CREATE BUTTON */}
                <button className="create-responder-button" onClick={() => setIsCreateModalOpen(true)}>
                    + Add New Responder
                </button>
            </div>

            {error && <div className="error-message">{error}</div>}

            <div className="responder-list-container">
                {loading && <p>Loading...</p>}
                
                {!loading && responders.length > 0 && responders
                    .filter(responder => responder.id !== user?.id)
                    .map(responder => (
                        <div key={responder.id} className="responder-card">
                            <div className="responder-left">
                                <h4>{responder.name}</h4>
                                <p className="responder-role">{responder.role}</p>
                            </div>
                            <div className="responder-right">
                                <div className="responder-details">
                                    <span>{responder.email}</span>
                                    <span className="location">{responder.location?.address || 'N/A'}</span>
                                </div>
                                {user?.role === 'admin' && (
                                    <>
                                        <button className="edit-responder-button" onClick={() => handleEdit(responder)}>Edit</button>
                                        <button className="delete-responder-button" onClick={() => handleDelete(responder.id, responder.name)}>Delete</button>
                                    </>
                                )}
                            </div>
                        </div>
                    ))}
                    
                {!loading && responders.length === 0 && <p>No other responders found.</p>}
            </div>

            {/* MODALS */}
            {isCreateModalOpen && (
                <ResponderCreateModal 
                    onClose={() => setIsCreateModalOpen(false)}
                    onCreate={handleCreateSuccess}
                />
            )}

            {isEditModalOpen && editingResponder && (
                <ResponderEditModal
                    responder={editingResponder}
                    onClose={() => setIsEditModalOpen(false)}
                    onUpdate={handleUpdateSuccess}
                />
            )}
        </Layout>
    );
};

export default ResponderList;