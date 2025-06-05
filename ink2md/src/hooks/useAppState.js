/**
 * @fileoverview useAppState hook - Custom hook for AppStateContext
 * 
 * Provides convenient access to global application state and actions.
 * This hook wraps the AppStateContext and provides additional utility functions
 * for common state operations.
 * 
 * @author Sarah Wolff
 * @version 0.5 beta
 */

import { useAppState as useAppStateContext } from '../contexts/AppStateContext'

/**
 * Custom hook for accessing and managing global application state
 * 
 * @returns {Object} App state and utility functions
 * @throws {Error} If used outside of AppStateProvider
 * 
 * @example
 * ```jsx
 * function MyComponent() {
 *   const { 
 *     isLoading, 
 *     activeTab, 
 *     setActiveTab, 
 *     showNotification,
 *     showError 
 *   } = useAppState()
 *   
 *   const handleTabChange = (tab) => {
 *     setActiveTab(tab)
 *   }
 *   
 *   const handleError = (error) => {
 *     showError('Something went wrong: ' + error.message)
 *   }
 *   
 *   return (
 *     <div>
 *       {isLoading && <div>Loading...</div>}
 *       <button onClick={() => handleTabChange('converter')}>
 *         Converter
 *       </button>
 *     </div>
 *   )
 * }
 * ```
 */
export function useAppState() {
  const context = useAppStateContext()
  
  if (!context) {
    throw new Error('useAppState must be used within an AppStateProvider')
  }

  // Destructure context for easier access
  const {
    // State
    isLoading,
    loadingProgress,
    loadingStage,
    totalPages,
    currentPage,
    activeTab,
    isMobile,
    sidebarOpen,
    notifications,
    error,
    success,
    
    // Actions
    setLoading,
    setLoadingProgress,
    setActiveTab,
    toggleSidebar,
    setSidebarOpen,
    addNotification,
    removeNotification,
    clearNotifications,
    setError,
    setSuccess,
    clearMessages,
    resetLoading
  } = context

  /**
   * Show a notification with automatic removal
   * @param {string} message - Notification message
   * @param {string} type - Notification type ('info' | 'success' | 'warning' | 'error')
   * @param {number} duration - Auto-remove duration in ms (default: 5000)
   * @returns {string} Notification ID for manual removal
   */
  const showNotification = (message, type = 'info', duration = 5000) => {
    const notification = {
      message,
      type,
      duration
    }
    
    addNotification(notification)
    
    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        removeNotification(notification.id)
      }, duration)
    }
    
    return notification.id
  }

  /**
   * Show an error notification
   * @param {string} message - Error message
   * @param {number} duration - Auto-remove duration in ms (default: 8000)
   * @returns {string} Notification ID
   */
  const showError = (message, duration = 8000) => {
    setError(message)
    return showNotification(message, 'error', duration)
  }

  /**
   * Show a success notification
   * @param {string} message - Success message
   * @param {number} duration - Auto-remove duration in ms (default: 5000)
   * @returns {string} Notification ID
   */
  const showSuccess = (message, duration = 5000) => {
    setSuccess(message)
    return showNotification(message, 'success', duration)
  }

  /**
   * Show a warning notification
   * @param {string} message - Warning message
   * @param {number} duration - Auto-remove duration in ms (default: 6000)
   * @returns {string} Notification ID
   */
  const showWarning = (message, duration = 6000) => {
    return showNotification(message, 'warning', duration)
  }

  /**
   * Show an info notification
   * @param {string} message - Info message
   * @param {number} duration - Auto-remove duration in ms (default: 5000)
   * @returns {string} Notification ID
   */
  const showInfo = (message, duration = 5000) => {
    return showNotification(message, 'info', duration)
  }

  /**
   * Start loading with optional progress tracking
   * @param {Object} options - Loading options
   * @param {string} options.stage - Loading stage description
   * @param {number} options.progress - Initial progress (0-100)
   * @param {number} options.totalPages - Total pages to process
   * @param {number} options.currentPage - Current page being processed
   */
  const startLoading = (options = {}) => {
    setLoading(true, options)
  }

  /**
   * Stop loading and reset all loading states
   */
  const stopLoading = () => {
    resetLoading()
  }

  /**
   * Update loading progress
   * @param {number} progress - Progress percentage (0-100)
   * @param {Object} options - Additional options
   * @param {string} options.stage - Current stage description
   * @param {number} options.totalPages - Total pages
   * @param {number} options.currentPage - Current page
   */
  const updateProgress = (progress, options = {}) => {
    setLoadingProgress(progress, options)
  }

  /**
   * Navigate to a specific tab
   * @param {string} tab - Tab name ('converter' | 'history' | 'prompts' | 'settings')
   */
  const navigateToTab = (tab) => {
    const validTabs = ['converter', 'history', 'prompts', 'settings']
    if (validTabs.includes(tab)) {
      setActiveTab(tab)
      
      // Auto-close sidebar on mobile after navigation
      if (isMobile && sidebarOpen) {
        setSidebarOpen(false)
      }
    } else {
      console.warn(`Invalid tab: ${tab}. Valid tabs are: ${validTabs.join(', ')}`)
    }
  }

  /**
   * Check if a specific tab is active
   * @param {string} tab - Tab name to check
   * @returns {boolean} Whether the tab is active
   */
  const isTabActive = (tab) => {
    return activeTab === tab
  }

  /**
   * Get loading progress as a formatted string
   * @returns {string} Formatted progress string
   */
  const getProgressText = () => {
    if (!isLoading) return ''
    
    let text = loadingStage || 'Loading...'
    
    if (loadingProgress > 0) {
      text += ` (${Math.round(loadingProgress)}%)`
    }
    
    if (totalPages > 0 && currentPage > 0) {
      text += ` - Page ${currentPage} of ${totalPages}`
    }
    
    return text
  }

  /**
   * Clear all messages and notifications
   */
  const clearAllMessages = () => {
    clearMessages()
    clearNotifications()
  }

  /**
   * Get current notification count
   * @returns {number} Number of active notifications
   */
  const getNotificationCount = () => {
    return notifications.length
  }

  /**
   * Check if there are any active notifications
   * @returns {boolean} Whether there are active notifications
   */
  const hasNotifications = () => {
    return notifications.length > 0
  }

  return {
    // State
    isLoading,
    loadingProgress,
    loadingStage,
    totalPages,
    currentPage,
    activeTab,
    isMobile,
    sidebarOpen,
    notifications,
    error,
    success,
    
    // Basic actions
    setLoading,
    setLoadingProgress,
    setActiveTab,
    toggleSidebar,
    setSidebarOpen,
    addNotification,
    removeNotification,
    clearNotifications,
    setError,
    setSuccess,
    clearMessages,
    resetLoading,
    
    // Utility functions
    showNotification,
    showError,
    showSuccess,
    showWarning,
    showInfo,
    startLoading,
    stopLoading,
    updateProgress,
    navigateToTab,
    isTabActive,
    getProgressText,
    clearAllMessages,
    getNotificationCount,
    hasNotifications
  }
}

export default useAppState