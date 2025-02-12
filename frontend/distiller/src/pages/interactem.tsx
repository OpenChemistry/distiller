//distiller/src/pages/interactem.tsx
import React from 'react';
import { InteractEM } from '@interactem/interactem';
import '@interactem/interactem/style.css';

const interactEMUrl =
  import.meta.env.VITE_INTERACTEM_URL ||
  `${window.location.origin}/interactem/api/v1`;
const natsServers =
  import.meta.env.VITE_NATS_SERVER_URL || `${window.location.origin}/nats`;

const InteractemPage: React.FC = () => {
  return (
    <div className="interactem-content">
      <InteractEM
        authMode="external"
        natsServers={natsServers}
        apiBaseURL={interactEMUrl}
      />
    </div>
  );
};

export default InteractemPage;
