/**
 * SettingsTab Component
 * 
 * @author Sarah Wolff
 * @version 0.5 beta
 * @description Temporary placeholder for the application settings interface
 * This will be fully implemented in later phases
 */

import React from 'react';
import '../common/TabPlaceholder.css';

const SettingsTab = () => {
  return (
    <div className="tab-placeholder">
      <div className="placeholder-content">
        <div className="placeholder-icon">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 0 1 0 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 0 1 0-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281Z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
          </svg>
        </div>
        <h2>Application Settings</h2>
        <p>Configure your preferences and application behavior.</p>
        <div className="placeholder-features">
          <div className="feature-item">
            <span className="feature-icon">🎨</span>
            <span>Theme & Appearance</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">🔧</span>
            <span>Conversion Settings</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">🔑</span>
            <span>API Configuration</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">📊</span>
            <span>Performance Options</span>
          </div>
        </div>
        <div className="placeholder-status">
          <span className="status-badge">Coming Soon in v0.5 Beta</span>
        </div>
      </div>
    </div>
  );
};

export default SettingsTab;