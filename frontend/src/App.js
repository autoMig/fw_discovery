import React, { useState } from 'react';
import FirewallDiscovery from './components/FirewallDiscovery';
import ConnectivityCheck from './components/ConnectivityCheck';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('discovery');

  return (
    <div className="App">
      <header className="App-header">
        <h1>🔥 Firewall Discovery Tool</h1>
        <p>Identify firewall platforms and check connectivity rules</p>
      </header>

      <div className="tab-container">
        <button
          className={`tab-button ${activeTab === 'discovery' ? 'active' : ''}`}
          onClick={() => setActiveTab('discovery')}
        >
          Discover Firewalls
        </button>
        <button
          className={`tab-button ${activeTab === 'connectivity' ? 'active' : ''}`}
          onClick={() => setActiveTab('connectivity')}
        >
          Check Connectivity
        </button>
      </div>

      <div className="content">
        {activeTab === 'discovery' ? (
          <FirewallDiscovery />
        ) : (
          <ConnectivityCheck />
        )}
      </div>

      <footer className="App-footer">
        <p>Firewall Discovery Tool v1.0.0</p>
      </footer>
    </div>
  );
}

export default App;
