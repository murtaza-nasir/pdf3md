import { useState, useEffect } from 'react'
import './Sidebar.css'

const Sidebar = ({ isOpen, history, onSelectHistory, selectedHistoryId, onClearHistory, onDeleteHistory, onClose }) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [filteredHistory, setFilteredHistory] = useState(history)

  useEffect(() => {
    console.log('[Sidebar] useEffect for search triggered. SearchTerm:', searchTerm);
    console.log('[Sidebar] History prop:', history);

    if (!searchTerm) {
      console.log('[Sidebar] No search term, setting filteredHistory to full history.');
      setFilteredHistory(history);
    } else {
      const lowerSearchTerm = searchTerm.toLowerCase();
      const filtered = history.filter(item => {
        const foundInFilename = item.filename && item.filename.toLowerCase().includes(lowerSearchTerm);
        const foundInMarkdown = item.markdown && item.markdown.toLowerCase().includes(lowerSearchTerm);
        return foundInFilename || foundInMarkdown;
      });
      console.log('[Sidebar] Filtered history based on search:', filtered);
      setFilteredHistory(filtered);
    }
  }, [searchTerm, history]);

  const formatRelativeTime = (timestamp) => {
    const now = new Date();
    const time = new Date(timestamp);

    // Handle invalid date
    if (isNaN(time.getTime())) {
      // console.error('[formatRelativeTime] Invalid timestamp encountered:', timestamp); // Optional: for deeper debugging
      return 'Invalid date';
    }

    const diffMs = now.getTime() - time.getTime();

    // If the timestamp is in the future
    if (diffMs < 0) {
      const futureDiffMinutes = Math.floor(-diffMs / (1000 * 60));
      if (futureDiffMinutes < 1) return 'Upcoming'; // Less than a minute in the future
      if (futureDiffMinutes < 60) return `In ${futureDiffMinutes}m`;
      const futureDiffHours = Math.floor(futureDiffMinutes / 60);
      if (futureDiffHours < 24) return `In ${futureDiffHours}h`;
      // For more than a day in the future, show the date
      return `On ${time.toLocaleDateString()}`;
    }

    // For past or current timestamps
    const diffInMinutes = Math.floor(diffMs / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now'; // 0-59 seconds ago
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`; // 1-59 minutes ago
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours}h ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays}d ago`;
    
    return time.toLocaleDateString(); // Older than 7 days
  };

  const groupHistoryByDate = (history) => {
    const groups = {
      today: [],
      yesterday: [],
      thisWeek: [],
      older: []
    }

    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)

    history.forEach(item => {
      const itemDate = new Date(item.timestamp)
      const itemDay = new Date(itemDate.getFullYear(), itemDate.getMonth(), itemDate.getDate())

      if (itemDay.getTime() === today.getTime()) {
        groups.today.push(item)
      } else if (itemDay.getTime() === yesterday.getTime()) {
        groups.yesterday.push(item)
      } else if (itemDate >= weekAgo) {
        groups.thisWeek.push(item)
      } else {
        groups.older.push(item)
      }
    })

    return groups
  }

  const groupedHistory = groupHistoryByDate(filteredHistory)

  const handleDeleteItem = (e, itemId) => {
    e.stopPropagation() // Prevent triggering the item selection
    if (window.confirm('Are you sure you want to delete this conversion from history?')) {
      onDeleteHistory(itemId)
    }
  }

  const renderHistoryGroup = (title, items) => {
    if (items.length === 0) return null

    return (
      <div className="history-group" key={title}>
        <div className="history-group-title">{title}</div>
        {items.map(item => (
          <div
            key={item.id}
            className={`history-item ${selectedHistoryId === item.id ? 'selected' : ''}`}
            onClick={() => onSelectHistory(item)}
          >
            <div className="history-item-header">
              <div className="file-section">
                <div className="file-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m6.75 12H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                  </svg>
                </div>
                {/* Delete button removed from here */}
              </div>
              <div className="file-info">
                <div className="filename" title={item.filename}>{item.filename}</div>
                <div className="file-meta">
                  <span className="file-size">{item.fileSize}</span>
                  {item.pageCount && (
                    <>
                      <span className="separator">•</span>
                      <span className="page-count">{item.pageCount} pages</span>
                    </>
                  )}
                </div>
              </div>
            </div>
            {/* Time element removed from here */}
            <div className="history-item-preview">
              {item.markdown.substring(0, 120)}...
            </div>
            <div className="history-item-actions">
              <div className="history-item-time-relocated">
                {/* SVG clock icon removed */}
                <span>{formatRelativeTime(item.timestamp)}</span>
              </div>
              <button
                className="delete-text-btn"
                onClick={(e) => handleDeleteItem(e, item.id)}
                title="Delete this conversion"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        <h2>History</h2>
        <div className="sidebar-actions">
          <button 
            className="mobile-close-btn"
            onClick={onClose}
            title="Close sidebar"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
          <button 
            className="clear-history-btn"
            onClick={onClearHistory}
            title="Clear all history"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
            </svg>
          </button>
        </div>
      </div>

      <div className="search-container">
        <div className="search-input-wrapper">
          <svg className="search-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
          <input
            type="text"
            placeholder="Search history..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          {searchTerm && (
            <button 
              className="clear-search-btn"
              onClick={() => setSearchTerm('')}
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      <div className="history-list">
        {filteredHistory.length === 0 ? (
          <div className="empty-state">
            {searchTerm ? (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
                </svg>
                <p>No results found</p>
                <span>Try a different search term</span>
              </>
            ) : (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                </svg>
                <p>No conversions yet</p>
                <span>Upload a PDF to get started</span>
              </>
            )}
          </div>
        ) : (
          <>
            {renderHistoryGroup('Today', groupedHistory.today)}
            {renderHistoryGroup('Yesterday', groupedHistory.yesterday)}
            {renderHistoryGroup('This Week', groupedHistory.thisWeek)}
            {renderHistoryGroup('Older', groupedHistory.older)}
          </>
        )}
      </div>
    </div>
  )
}

export default Sidebar
