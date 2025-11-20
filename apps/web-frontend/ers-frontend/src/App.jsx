import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import MapView from './pages/MapView';
import ResponseHistory from './pages/ResponseHistory';
import Profile from './pages/Profile';
import ResponderList from './pages/ResponderList';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/map-view" element={<MapView />} />
            <Route path="/history" element={<ResponseHistory />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/responders" element={<ResponderList /> } />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;