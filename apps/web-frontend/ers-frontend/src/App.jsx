import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Page Imports
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import MapView from './pages/MapView';
import ResponseHistory from './pages/ResponseHistory';
import Profile from './pages/Profile';

function App() {
  return (
    // <BrowserRouter> MUST be on the outside
    <BrowserRouter>
      {/* <AuthProvider> MUST be on the inside */}
      <AuthProvider>
        <Routes>
          {/* Public Login Page */}
          <Route path="/login" element={<LoginPage />} />
          
          {/* Protected Routes (Require Login) */}
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/map-view" element={<MapView />} />
            <Route path="/history" element={<ResponseHistory />} />
            <Route path="/profile" element={<Profile />} />
            
            {/* Default redirect to dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Route>
          
          {/* Catch-all for unknown routes */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;