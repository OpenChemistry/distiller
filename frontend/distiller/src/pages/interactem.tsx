//distiller/src/pages/interactem.tsx
import React from 'react';
import { InteractEM } from '@interactem/interactem';
import '@interactem/interactem/style.css';

const interactemApiUrl =
  import.meta.env.VITE_INTERACTEM_URL ||
  `${window.location.origin}/interactem/`;
const natsServers =
  import.meta.env.VITE_NATS_SERVER_URL || `${window.location.origin}/interactem/nats`;

const InteractemPage: React.FC = () => {
  return (
    <div className="interactem-content">
      <InteractEM
        authMode="external"
        natsServers={natsServers}
        apiBaseURL={interactemApiUrl}
      />
    </div>
  );
};

export default InteractemPage;
