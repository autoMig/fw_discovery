import React, { useState } from 'react';
import axios from 'axios';
import './ConnectivityCheck.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function ConnectivityCheck() {
  const [formData, setFormData] = useState({
    source: '',
    destination: '',
    port: '',
    protocol: 'TCP'
  });
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/check-connectivity`,
        {
          source: formData.source,
          destination: formData.destination,
          port: parseInt(formData.port),
          protocol: formData.protocol
        }
      );

      setResults(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred while checking connectivity');
      console.error('Connectivity check error:', err);
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

  const renderApplicableFirewalls = () => {
    if (!results) return null;

    const sourceFw = Object.entries(results.source_firewalls.summary || {})
      .filter(([_, active]) => active)
      .map(([fw, _]) => fw);

    const destFw = Object.entries(results.destination_firewalls.summary || {})
      .filter(([_, active]) => active)
      .map(([fw, _]) => fw);

    return (
      <div className="applicable-firewalls-section">
        <h3>🔍 Applicable Firewalls</h3>
        <div className="firewall-groups">
          <div className="firewall-group">
            <h4>Source ({results.source})</h4>
            {sourceFw.length > 0 ? (
              <div className="firewall-badges">
                {sourceFw.map(fw => (
                  <div key={fw}>{renderFirewallBadge(fw)}</div>
                ))}
              </div>
            ) : (
              <p className="no-firewalls">No firewalls detected</p>
            )}
          </div>
          <div className="firewall-group">
            <h4>Destination ({results.destination})</h4>
            {destFw.length > 0 ? (
              <div className="firewall-badges">
                {destFw.map(fw => (
                  <div key={fw}>{renderFirewallBadge(fw)}</div>
                ))}
              </div>
            ) : (
              <p className="no-firewalls">No firewalls detected</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderRuleResults = () => {
    if (!results?.rule_results) return null;

    return (
      <div className="rule-results-section">
        <h3>📋 Rule Check Results</h3>
        
        {Object.entries(results.rule_results).map(([firewallType, result]) => {
          if (!result) return null;

          return (
            <div key={firewallType} className="rule-result-card">
              <div className="rule-result-header">
                {renderFirewallBadge(firewallType)}
              </div>

              {result.status === 'success' && (
                <>
                  <div className="connection-details">
                    <p>
                      <strong>Connection:</strong> {result.source_ip} → {result.dest_ip}:{result.port}/{result.protocol}
                    </p>
                  </div>

                  {result.policy_check && (
                    <div className="policy-check">
                      <h4>Policy Check</h4>
                      <div className={`verdict ${result.policy_check.allowed ? 'allowed' : 'blocked'}`}>
                        {result.policy_check.allowed ? '✅ Allowed' : '❌ Blocked'}
                      </div>
                      {result.policy_check.decision && (
                        <p><strong>Decision:</strong> {result.policy_check.decision}</p>
                      )}
                    </div>
                  )}

                  {result.matching_rules && result.matching_rules.length > 0 && (
                    <div className="matching-rules">
                      <h4>Matching Rules ({result.rule_count})</h4>
                      {result.matching_rules.map((rule, index) => (
                        <div key={index} className="rule-item">
                          <div className="rule-name">
                            <strong>{rule.rule_name || `Rule ${rule.rule_id}`}</strong>
                            {rule.enabled !== undefined && (
                              <span className={`rule-status ${rule.enabled ? 'enabled' : 'disabled'}`}>
                                {rule.enabled ? 'Enabled' : 'Disabled'}
                              </span>
                            )}
                          </div>
                          <div className="rule-details">
                            <div><strong>Rule ID:</strong> {rule.rule_id}</div>
                            <div><strong>Action:</strong> {rule.action}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}

              {result.status === 'not_implemented' && (
                <div className="info-message">
                  <p>{result.message}</p>
                </div>
              )}

              {result.status === 'error' && (
                <div className="error-message">
                  <p>{result.message}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="connectivity-check">
      <h2>Check Connectivity Rules</h2>
      <p className="description">
        Check which firewall rules permit traffic between a source and destination.
      </p>

      <form onSubmit={handleSubmit} className="connectivity-form">
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="source">Source</label>
            <input
              type="text"
              id="source"
              name="source"
              value={formData.source}
              onChange={handleInputChange}
              placeholder="Application name or hostname"
              required
            />
            <small>Enter an application name or hostname</small>
          </div>

          <div className="form-group">
            <label htmlFor="destination">Destination</label>
            <input
              type="text"
              id="destination"
              name="destination"
              value={formData.destination}
              onChange={handleInputChange}
              placeholder="Application name or hostname"
              required
            />
            <small>Enter an application name or hostname</small>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="port">Port</label>
            <input
              type="number"
              id="port"
              name="port"
              value={formData.port}
              onChange={handleInputChange}
              placeholder="e.g., 443"
              min="1"
              max="65535"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="protocol">Protocol</label>
            <select
              id="protocol"
              name="protocol"
              value={formData.protocol}
              onChange={handleInputChange}
            >
              <option value="TCP">TCP</option>
              <option value="UDP">UDP</option>
            </select>
          </div>
        </div>

        <button type="submit" disabled={loading} className="submit-button">
          {loading ? 'Checking...' : 'Check Connectivity'}
        </button>
      </form>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {results && (
        <div className="results-container">
          {renderApplicableFirewalls()}
          {renderRuleResults()}
        </div>
      )}
    </div>
  );
}

export default ConnectivityCheck;
