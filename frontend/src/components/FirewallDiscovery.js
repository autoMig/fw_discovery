import React, { useState } from 'react';
import axios from 'axios';
import './FirewallDiscovery.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function FirewallDiscovery() {
  const [searchType, setSearchType] = useState('application');
  const [searchValue, setSearchValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const payload = searchType === 'application' 
        ? { application_name: searchValue }
        : { hostname: searchValue };

      const response = await axios.post(
        `${API_BASE_URL}/api/v1/discover-firewalls`,
        payload
      );

      setResults(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred while searching');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const renderFirewallBadge = (firewallType) => {
    const badges = {
      external_checkpoint: { label: 'External Checkpoint', color: '#e74c3c' },
      internal_checkpoint: { label: 'Internal Checkpoint', color: '#e67e22' },
      illumio: { label: 'Illumio', color: '#3498db' },
      nsx: { label: 'NSX', color: '#2ecc71' }
    };

    const badge = badges[firewallType];
    return (
      <span 
        className="firewall-badge" 
        style={{ backgroundColor: badge.color }}
      >
        {badge.label}
      </span>
    );
  };

  const renderSummary = () => {
    if (!results?.summary) return null;

    const activeFirewalls = Object.entries(results.summary)
      .filter(([_, active]) => active)
      .map(([fw, _]) => fw);

    if (activeFirewalls.length === 0) {
      return (
        <div className="summary-card warning">
          <h3>⚠️ No Firewalls Detected</h3>
          <p>No firewall platforms were identified for this {searchType}.</p>
        </div>
      );
    }

    return (
      <div className="summary-card">
        <h3>📊 Summary</h3>
        <p>The following firewall platforms apply to this {searchType}:</p>
        <div className="firewall-badges">
          {activeFirewalls.map(fw => (
            <div key={fw}>{renderFirewallBadge(fw)}</div>
          ))}
        </div>
      </div>
    );
  };

  const renderHostDetails = () => {
    if (!results?.hosts || results.hosts.length === 0) return null;

    return (
      <div className="hosts-container">
        <h3>🖥️ Host Details</h3>
        {results.hosts.map((host, index) => (
          <div key={index} className="host-card">
            <div className="host-header">
              <h4>{host.hostname}</h4>
              <span className="ip-address">{host.ip_address}</span>
            </div>
            
            <div className="host-properties">
              <div className="property">
                <strong>Location:</strong> {host.location}
              </div>
              <div className="property">
                <strong>Network Zone:</strong> {host.network_zone}
              </div>
              <div className="property">
                <strong>Platform:</strong> {host.platform}
              </div>
              <div className="property">
                <strong>OS Type:</strong> {host.os_type}
              </div>
            </div>

            {host.applicable_firewalls.length > 0 && (
              <>
                <div className="host-firewalls">
                  <strong>Applicable Firewalls:</strong>
                  <div className="firewall-badges">
                    {host.applicable_firewalls.map(fw => (
                      <div key={fw}>{renderFirewallBadge(fw)}</div>
                    ))}
                  </div>
                </div>

                <div className="firewall-details">
                  {Object.entries(host.firewall_details).map(([fw, details]) => (
                    <div key={fw} className="firewall-detail-item">
                      <strong>{details.platform}:</strong> {details.reason}
                      {details.operating_mode && (
                        <span className="operating-mode">
                          {' '}(Mode: {details.operating_mode})
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="firewall-discovery">
      <h2>Discover Firewall Platforms</h2>
      <p className="description">
        Find out which firewall platforms are used by your application or host.
      </p>

      <form onSubmit={handleSearch} className="search-form">
        <div className="search-type-selector">
          <label className={searchType === 'application' ? 'active' : ''}>
            <input
              type="radio"
              value="application"
              checked={searchType === 'application'}
              onChange={(e) => setSearchType(e.target.value)}
            />
            Application Name
          </label>
          <label className={searchType === 'hostname' ? 'active' : ''}>
            <input
              type="radio"
              value="hostname"
              checked={searchType === 'hostname'}
              onChange={(e) => setSearchType(e.target.value)}
            />
            Hostname
          </label>
        </div>

        <div className="search-input-group">
          <input
            type="text"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder={
              searchType === 'application' 
                ? 'Enter application name (e.g., MyBusinessApp)' 
                : 'Enter hostname (e.g., server01.example.com)'
            }
            required
            className="search-input"
          />
          <button type="submit" disabled={loading} className="search-button">
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {results && (
        <div className="results-container">
          {renderSummary()}
          {renderHostDetails()}
        </div>
      )}
    </div>
  );
}

export default FirewallDiscovery;
