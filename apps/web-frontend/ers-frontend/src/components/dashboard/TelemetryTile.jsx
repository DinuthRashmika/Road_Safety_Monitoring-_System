import React from 'react';

const TelemetryTile = ({ title, value }) => {
  return (
    <div className="telemetry-tile">
      <span className="tile-title">{title}</span>
      <span className="tile-value">{value}</span>
    </div>
  );
};

export default TelemetryTile;