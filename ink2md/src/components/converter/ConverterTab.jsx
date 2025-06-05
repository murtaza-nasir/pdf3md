/**
 * ConverterTab Component
 * 
 * @author Sarah Wolff
 * @version 0.5 beta
 * @description Temporary placeholder for the PDF to Markdown converter interface
 * This will be fully implemented in later phases
 */

import React from 'react';
import '../common/TabPlaceholder.css';

const ConverterTab = () => {
  return (
    <div className="tab-placeholder">
      <div className="placeholder-content">
        <div className="placeholder-icon">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m6.75 12H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
          </svg>
        </div>
        <h2>PDF to Markdown Converter</h2>
        <p>Convert your PDF documents to clean, formatted Markdown text.</p>
        <div className="placeholder-features">
          <div className="feature-item">
            <span className="feature-icon">📄</span>
            <span>Drag & Drop PDF Upload</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">⚡</span>
            <span>Fast AI-Powered Conversion</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">📝</span>
            <span>Clean Markdown Output</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">💾</span>
            <span>Auto-Save to History</span>
          </div>
        </div>
        <div className="placeholder-status">
          <span className="status-badge">Coming Soon in v0.5 Beta</span>
        </div>
      </div>
    </div>
  );
};

export default ConverterTab;