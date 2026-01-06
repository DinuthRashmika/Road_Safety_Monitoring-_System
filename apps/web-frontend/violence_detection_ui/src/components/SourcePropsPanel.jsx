import React from 'react';
import './../styles/SourcePropsPanel.css';
import { useNavigate } from 'react-router-dom';

function SourcesPropsPanel({ isOpen, onClose, camera, videoInfo, videoSource  }) {

  const navigate = useNavigate();

  const handleStartDetection = () => {
    // Determine the source path
    let sourcePath = null;
    
    if (videoSource && videoInfo) {
      // If videoSource prop is passed (from manual input)
      sourcePath = videoSource;
    } else if (camera) {
      // If camera is passed, get its source path
      sourcePath = camera.stream_url || camera.rtsp_url || camera.source_path;
    }

    if (!sourcePath) {
      alert("No source path available!");
      return;
    }

    // Close the panel
    onClose();

    // Navigate to detection page with source info
    navigate('/detection-monitering', {
      state: {
        videoSource: sourcePath,
        videoInfo: videoInfo,
        cameraInfo: camera,
        isCamera: !!camera
      }
    });
  };


  return (
    <>
      {/* Right Side Panel - Split Screen Style */}
      <div className={`details-panel ${isOpen ? 'open' : ''}`}>
        <div className="panel-header">
          <h3>Source Details</h3>
          <button className="close-btn" onClick={onClose}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div className="panel-content">
          {camera && (
            <>
              <div className="detail-section">
                <div className="detail-header">
                  <h4>Basic Information</h4>
                  <span className={`status-badge ${camera.status === "ONLINE" ? "online" : "offline"}`}>
                    {camera.status}
                  </span>
                </div>
                
                <div className="detail-row">
                  <span className="detail-label">Name:</span>
                  <span className="detail-value">{camera.name}</span>
                </div>
                
                <div className="detail-row">
                  <span className="detail-label">ID:</span>
                  <span className="detail-value">{camera.id}</span>
                </div>
                
                <div className="detail-row">
                  <span className="detail-label">Status:</span>
                  <span className="detail-status">{camera.status}</span>
                </div>
              </div>

              <div className="detail-section">
                <h4>Source Properties</h4>
                <div className="detail-row">
                  <span className="detail-label">Location:</span>
                  <span className="detail-value">{camera.location || 'N/A'}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Model:</span>
                  <span className="detail-value">{camera.model || 'N/A'}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">IP Address:</span>
                  <span className="detail-value">{camera.ipAddress || 'N/A'}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Resolution:</span>
                  <span className="detail-value">{camera.resolution || 'N/A'}</span>
                </div>
              </div>
            </>
          )}

          {/* Video Properties Section */}
          {videoInfo && (
            <>
              {/* Title OUTSIDE the rectangle */}
              <h4 className="section-title">Video Properties</h4>

              {/* Rectangle */}
              <div className="detail-section">
                <div className="detail-row">
                  <span className="detail-label">FPS:</span>
                  <span className="detail-value">{videoInfo.fps || 'N/A'}</span>
                </div>

                <div className="detail-row">
                  <span className="detail-label">Total Frames:</span>
                  <span className="detail-value">
                    {videoInfo.total_frames || videoInfo.totalFrames || 'N/A'}
                  </span>
                </div>

                <div className="detail-row">
                  <span className="detail-label">Duration:</span>
                  <span className="detail-value">
                    {videoInfo.duration ? `${videoInfo.duration.toFixed(2)}s` : 'N/A'}
                  </span>
                </div>

                <div className="detail-row">
                  <span className="detail-label">Resolution: (Height x Width)</span>
                  <span className="detail-value">
                    {videoInfo.width} × {videoInfo.height}
                  </span>
                </div>

                {videoInfo.bitrate && (
                  <div className="detail-row">
                    <span className="detail-label">Bitrate:</span>
                    <span className="detail-value">{videoInfo.bitrate}</span>
                  </div>
                )}

                {videoInfo.codec && (
                  <div className="detail-row">
                    <span className="detail-label">Codec:</span>
                    <span className="detail-value">{videoInfo.codec}</span>
                  </div>
                )}
              </div>
            </>
          )}


          {/* Action buttons in panel*/}
          {camera &&(
            <div className="panel-actions">
              <button className="btn-red"  onClick={onClose}>Close</button>
              <button className="btn-dark"  onClick={handleStartDetection}>Start Detection</button>
            </div>
          )}

          {videoInfo &&(
            <div className="panel-actions">
              <button className="btn-red"  onClick={onClose}>Close</button>
              <button className="btn-dark"  onClick={handleStartDetection}>Start Detection</button>
            </div>
          )}

        </div>
      </div>
    </>
  );
}

export default SourcesPropsPanel;