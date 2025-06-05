import React, { useState, useEffect } from 'react';
import './MultiFileUploadStatus.css';

const getStatusIcon = (status) => {
  switch (status) {
    case 'Queued':
      return '🕒'; // Clock
    case 'Uploading':
      return '⬆️'; // Up arrow
    case 'Processing':
      return '⚙️'; // Gear
    case 'Completed':
      return '✅'; // Check mark
    case 'Error':
      return '❌'; // Cross mark
    case 'Skipped':
      return '⏭️'; // Skip track
    default:
      return '❓'; // Question mark
  }
};

const MultiFileUploadStatus = ({ fileStates, onClearCompleted, onRetryFile, onRemoveFile }) => {
  const [isMinimized, setIsMinimized] = useState(false);

  if (!fileStates || fileStates.length === 0) {
    return null;
  }

  const toggleMinimize = () => setIsMinimized(!isMinimized);

  const completedCount = fileStates.filter(f => f.status === 'Completed').length;
  const errorCount = fileStates.filter(f => f.status === 'Error').length;
  const processingCount = fileStates.filter(f => f.status === 'Uploading' || f.status === 'Processing' || f.status === 'Queued').length;
  const totalFiles = fileStates.length;
  const allDoneOrSkipped = fileStates.every(f => f.status === 'Completed' || f.status === 'Error' || f.status === 'Skipped');


  let summaryText = `${processingCount} processing, ${completedCount} done, ${errorCount} errors.`;
  if (processingCount === 0 && errorCount === 0 && completedCount > 0) {
    summaryText = `${completedCount} file(s) completed successfully.`;
  } else if (processingCount === 0 && errorCount > 0 && completedCount === 0) {
    summaryText = `${errorCount} file(s) failed.`;
  } else if (processingCount === 0 && errorCount > 0 && completedCount > 0) {
    summaryText = `${completedCount} completed, ${errorCount} failed.`;
  } else if (processingCount === 0 && allDoneOrSkipped && completedCount === 0 && errorCount === 0) {
    summaryText = "All files processed/skipped.";
  }


  return (
    <div className={`multi-file-status-modal ${isMinimized ? 'minimized' : ''}`}>
      <div className="modal-header" onClick={toggleMinimize} title={isMinimized ? "Expand" : "Minimize"}>
        <h4>{isMinimized ? `Uploads: ${completedCount}/${totalFiles} done` : 'Upload Status'}</h4>
        {isMinimized && <span className="summary-info">{summaryText}</span>}
        <div className="action-buttons">
          <button onClick={(e) => { e.stopPropagation(); toggleMinimize(); }} className="toggle-minimize-btn" title={isMinimized ? 'Expand' : 'Minimize'}>
            {isMinimized ? (
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" width="18" height="18">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m4.5 11.25h-4.5m4.5 0v-4.5m0 .75-5.25-5.25" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" width="18" height="18">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 9V4.5M9 9H4.5M9 9 3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5M15 15l5.25 5.25" />
              </svg>
            )}
          </button>
          {!isMinimized && allDoneOrSkipped && onClearCompleted && (
            <button 
              onClick={(e) => { e.stopPropagation(); onClearCompleted(); }} 
              className="clear-all-btn" 
              title="Clear all statuses"
            >
              Clear All
            </button>
          )}
        </div>
      </div>
      {!isMinimized && (
        <ul className="file-status-list">
          {fileStates.map((file, index) => (
            <li key={file.name + index} className={`file-status-item status-${file.status?.toLowerCase()}`}>
              <span className="status-icon">{getStatusIcon(file.status)}</span>
              <div className="file-details-wrapper">
                <div className="file-name-size">
                  <span className="file-name" title={file.name}>{file.name}</span>
                  <span className="file-size">({(file.size / (1024 * 1024)).toFixed(2)} MB)</span>
                </div>
                <div className="status-and-progress">
                  <span className="status-text">{file.stage || file.status}</span>
                  {(file.status === 'Uploading' || file.status === 'Processing') && file.progress > 0 && (
                    <span className="status-progress-text">({file.progress}%)</span>
                  )}
                </div>
                {(file.status === 'Uploading' || file.status === 'Processing') && (
                  <div className="progress-bar-container-thin">
                    <div className="progress-bar-fill-thin" style={{ width: `${file.progress}%` }}></div>
                  </div>
                )}
                 {file.status === 'Error' && file.error && (
                  <span className="status-text status-error" title={file.error}>Error: {file.error.length > 30 ? file.error.substring(0,27) + '...' : file.error}</span>
                )}
              </div>
              <div className="file-item-actions">
                {file.status === 'Error' && onRetryFile && (
                  <button onClick={() => onRetryFile(file.originalFile || file)} className="retry-btn" title="Retry upload">
                    Retry
                  </button>
                )}
                {(file.status === 'Completed' || file.status === 'Error' || file.status === 'Skipped') && onRemoveFile && (
                   <button onClick={() => onRemoveFile(file.name)} className="remove-btn" title="Remove from list">
                     Remove
                   </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default MultiFileUploadStatus;
