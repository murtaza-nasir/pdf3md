/**
 * @fileoverview AppStateContext - Global application state management
 * 
 * Manages global application state including:
 * - Loading states and progress tracking
 * - Notification system
 * - Error handling and display
 * - Active tab state for navigation
 * - Mobile/desktop detection
 * - Sidebar state management
 * 
 * @author Sarah Wolff
 * @version 0.5
 */

import { createContext, useContext, useReducer, useEffect, useCallback } from 'react'

/**
 * @typedef {Object} AppState
 * @property {boolean} isLoading - Global loading state
 * @property {number} loadingProgress - Progress percentage (0-100)
 * @property {string} loadingStage - Current loading stage description
 * @property {number} totalPages - Total pages being processed
 * @property {number} currentPage - Current page being processed
 * @property {string} activeTab - Currently active tab ('converter' | 'history' | 'prompts' | 'settings')
 * @property {boolean} isMobile - Mobile device detection
 * @property {boolean} sidebarOpen - Sidebar visibility state
 * @property {Array<Object>} notifications - Array of notification objects
 * @property {string|null} error - Current error message
 * @property {string|null} success - Current success message
 */

/**
 * @typedef {Object} AppStateActions
 * @property {Function} setLoading - Set global loading state
 * @property {Function} setLoadingProgress - Update loading progress
 * @property {Function} setActiveTab - Change active tab
 * @property {Function} toggleSidebar - Toggle sidebar visibility
 * @property {Function} setSidebarOpen - Set sidebar open state
 * @property {Function} addNotification - Add a new notification
 * @property {Function} removeNotification - Remove notification by ID
 * @property {Function} clearNotifications - Clear all notifications
 * @property {Function} setError - Set error message
 * @property {Function} setSuccess - Set success message
 * @property {Function} clearMessages - Clear error and success messages
 */

// Initial state
const initialState = {
  isLoading: false,
  loadingProgress: 0,
  loadingStage: '',
  totalPages: 0,
  currentPage: 0,
  activeTab: 'converter',
  isMobile: false,
  sidebarOpen: true,
  notifications: [],
  error: null,
  success: null
}

// Action types
const ActionTypes = {
  SET_LOADING: 'SET_LOADING',
  SET_LOADING_PROGRESS: 'SET_LOADING_PROGRESS',
  SET_ACTIVE_TAB: 'SET_ACTIVE_TAB',
  SET_MOBILE: 'SET_MOBILE',
  SET_SIDEBAR_OPEN: 'SET_SIDEBAR_OPEN',
  ADD_NOTIFICATION: 'ADD_NOTIFICATION',
  REMOVE_NOTIFICATION: 'REMOVE_NOTIFICATION',
  CLEAR_NOTIFICATIONS: 'CLEAR_NOTIFICATIONS',
  SET_ERROR: 'SET_ERROR',
  SET_SUCCESS: 'SET_SUCCESS',
  CLEAR_MESSAGES: 'CLEAR_MESSAGES',
  RESET_LOADING: 'RESET_LOADING'
}

/**
 * App state reducer
 * @param {AppState} state - Current state
 * @param {Object} action - Action object with type and payload
 * @returns {AppState} New state
 */
function appStateReducer(state, action) {
  switch (action.type) {
    case ActionTypes.SET_LOADING:
      return {
        ...state,
        isLoading: action.payload.isLoading,
        loadingProgress: action.payload.progress || state.loadingProgress,
        loadingStage: action.payload.stage || state.loadingStage,
        totalPages: action.payload.totalPages || state.totalPages,
        currentPage: action.payload.currentPage || state.currentPage
      }

    case ActionTypes.SET_LOADING_PROGRESS:
      return {
        ...state,
        loadingProgress: action.payload.progress,
        loadingStage: action.payload.stage || state.loadingStage,
        totalPages: action.payload.totalPages || state.totalPages,
        currentPage: action.payload.currentPage || state.currentPage
      }

    case ActionTypes.SET_ACTIVE_TAB:
      return {
        ...state,
        activeTab: action.payload
      }

    case ActionTypes.SET_MOBILE:
      return {
        ...state,
        isMobile: action.payload
      }

    case ActionTypes.SET_SIDEBAR_OPEN:
      return {
        ...state,
        sidebarOpen: action.payload
      }

    case ActionTypes.ADD_NOTIFICATION:
      return {
        ...state,
        notifications: [...state.notifications, {
          id: Date.now() + Math.random(),
          timestamp: new Date().toISOString(),
          ...action.payload
        }]
      }

    case ActionTypes.REMOVE_NOTIFICATION:
      return {
        ...state,
        notifications: state.notifications.filter(n => n.id !== action.payload)
      }

    case ActionTypes.CLEAR_NOTIFICATIONS:
      return {
        ...state,
        notifications: []
      }

    case ActionTypes.SET_ERROR:
      return {
        ...state,
        error: action.payload,
        success: null // Clear success when setting error
      }

    case ActionTypes.SET_SUCCESS:
      return {
        ...state,
        success: action.payload,
        error: null // Clear error when setting success
      }

    case ActionTypes.CLEAR_MESSAGES:
      return {
        ...state,
        error: null,
        success: null
      }

    case ActionTypes.RESET_LOADING:
      return {
        ...state,
        isLoading: false,
        loadingProgress: 0,
        loadingStage: '',
        totalPages: 0,
        currentPage: 0
      }

    default:
      return state
  }
}

// Create context
const AppStateContext = createContext(null)

/**
 * AppStateProvider component
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components
 * @returns {JSX.Element} Provider component
 */
export function AppStateProvider({ children }) {
  const [state, dispatch] = useReducer(appStateReducer, initialState)

  // Mobile detection effect
  useEffect(() => {
    const checkMobile = () => {
      const isMobile = window.innerWidth <= 768
      dispatch({ type: ActionTypes.SET_MOBILE, payload: isMobile })
      
      // Auto-close sidebar on mobile
      if (isMobile && state.sidebarOpen) {
        dispatch({ type: ActionTypes.SET_SIDEBAR_OPEN, payload: false })
      }
    }

    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [state.sidebarOpen])

  // Auto-clear messages after timeout
  useEffect(() => {
    if (state.error || state.success) {
      const timer = setTimeout(() => {
        dispatch({ type: ActionTypes.CLEAR_MESSAGES })
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [state.error, state.success])

  // Action creators
  const actions = {
    /**
     * Set global loading state
     * @param {boolean} isLoading - Loading state
     * @param {Object} options - Additional loading options
     */
    setLoading: useCallback((isLoading, options = {}) => {
      dispatch({
        type: ActionTypes.SET_LOADING,
        payload: { isLoading, ...options }
      })
    }, []),

    /**
     * Update loading progress
     * @param {number} progress - Progress percentage (0-100)
     * @param {Object} options - Additional progress options
     */
    setLoadingProgress: useCallback((progress, options = {}) => {
      dispatch({
        type: ActionTypes.SET_LOADING_PROGRESS,
        payload: { progress, ...options }
      })
    }, []),

    /**
     * Change active tab
     * @param {string} tab - Tab name
     */
    setActiveTab: useCallback((tab) => {
      dispatch({ type: ActionTypes.SET_ACTIVE_TAB, payload: tab })
    }, []),

    /**
     * Toggle sidebar visibility
     */
    toggleSidebar: useCallback(() => {
      dispatch({ type: ActionTypes.SET_SIDEBAR_OPEN, payload: !state.sidebarOpen })
    }, [state.sidebarOpen]),

    /**
     * Set sidebar open state
     * @param {boolean} open - Sidebar open state
     */
    setSidebarOpen: useCallback((open) => {
      dispatch({ type: ActionTypes.SET_SIDEBAR_OPEN, payload: open })
    }, []),

    /**
     * Add notification
     * @param {Object} notification - Notification object
     */
    addNotification: useCallback((notification) => {
      dispatch({ type: ActionTypes.ADD_NOTIFICATION, payload: notification })
    }, []),

    /**
     * Remove notification by ID
     * @param {string|number} id - Notification ID
     */
    removeNotification: useCallback((id) => {
      dispatch({ type: ActionTypes.REMOVE_NOTIFICATION, payload: id })
    }, []),

    /**
     * Clear all notifications
     */
    clearNotifications: useCallback(() => {
      dispatch({ type: ActionTypes.CLEAR_NOTIFICATIONS })
    }, []),

    /**
     * Set error message
     * @param {string|null} error - Error message
     */
    setError: useCallback((error) => {
      dispatch({ type: ActionTypes.SET_ERROR, payload: error })
    }, []),

    /**
     * Set success message
     * @param {string|null} success - Success message
     */
    setSuccess: useCallback((success) => {
      dispatch({ type: ActionTypes.SET_SUCCESS, payload: success })
    }, []),

    /**
     * Clear error and success messages
     */
    clearMessages: useCallback(() => {
      dispatch({ type: ActionTypes.CLEAR_MESSAGES })
    }, []),

    /**
     * Reset all loading states
     */
    resetLoading: useCallback(() => {
      dispatch({ type: ActionTypes.RESET_LOADING })
    }, [])
  }

  const contextValue = {
    ...state,
    ...actions
  }

  return (
    <AppStateContext.Provider value={contextValue}>
      {children}
    </AppStateContext.Provider>
  )
}

/**
 * Custom hook to use app state context
 * @returns {AppState & AppStateActions} App state and actions
 * @throws {Error} If used outside of AppStateProvider
 */
export function useAppState() {
  const context = useContext(AppStateContext)
  if (!context) {
    throw new Error('useAppState must be used within an AppStateProvider')
  }
  return context
}

export default AppStateContext