/**
 * @fileoverview SettingsContext - Configuration and settings management
 * 
 * Manages application settings including:
 * - AI provider configurations
 * - Application preferences
 * - User settings persistence
 * - Backend configuration synchronization
 * - Settings validation and testing
 * 
 * @author Sarah Wolff
 * @version 0.5
 */

import { createContext, useContext, useReducer, useEffect, useRef, useCallback } from 'react'

/**
 * @typedef {Object} AIProviderConfig
 * @property {string} display_name - Human-readable provider name
 * @property {string} type - Provider type ('anthropic' | 'ollama')
 * @property {string} api_key - API key (for external providers)
 * @property {string} api_base_url - Base URL for API
 * @property {string} model - Model identifier
 * @property {boolean} is_htr_capable - Can perform handwriting recognition
 * @property {boolean} is_formatting_capable - Can perform text formatting
 * @property {boolean} is_vlm_capable - Vision-language model capability
 * @property {boolean} enabled - Whether provider is enabled
 */

/**
 * @typedef {Object} AppSettings
 * @property {string} monitored_input_dir - Input directory path
 * @property {string} processed_output_dir - Output directory path
 * @property {string} default_output_pattern - Default filename pattern
 * @property {string|null} custom_output_pattern - Custom filename pattern
 * @property {number} global_retry_attempts - Number of retry attempts
 * @property {boolean} enable_directory_monitoring - Directory monitoring flag
 */

/**
 * @typedef {Object} ActiveServices
 * @property {string} htr_provider_id - Active HTR provider ID
 * @property {string} formatting_provider_id - Active formatting provider ID
 */

/**
 * @typedef {Object} SettingsState
 * @property {Object|null} config - Full configuration object
 * @property {Object<string, AIProviderConfig>} aiProviders - AI provider configurations
 * @property {AppSettings} appSettings - Application settings
 * @property {ActiveServices} activeServices - Active service providers
 * @property {boolean} isLoading - Loading state
 * @property {boolean} isSaving - Saving state
 * @property {Object<string, boolean>} testing - Provider testing states
 * @property {Object<string, Object>} testResults - Provider test results
 * @property {string|null} error - Current error message
 * @property {string|null} success - Current success message
 * @property {Object<string, boolean>} showApiKeys - API key visibility states
 */

/**
 * @typedef {Object} SettingsActions
 * @property {Function} loadConfig - Load configuration from backend
 * @property {Function} saveConfig - Save configuration to backend
 * @property {Function} updateProviderConfig - Update AI provider configuration
 * @property {Function} updateAppSettings - Update application settings
 * @property {Function} updateActiveServices - Update active services
 * @property {Function} testProvider - Test specific AI provider
 * @property {Function} testAllProviders - Test all AI providers
 * @property {Function} toggleApiKeyVisibility - Toggle API key visibility
 * @property {Function} resetToDefaults - Reset all settings to defaults
 * @property {Function} clearError - Clear error message
 * @property {Function} clearSuccess - Clear success message
 */

// Initial state
const initialState = {
  config: null,
  aiProviders: {},
  appSettings: {
    monitored_input_dir: "/app/input_pdfs",
    processed_output_dir: "/app/output_markdown",
    default_output_pattern: "YYYY-MM-DD-[OriginalFileName].md",
    custom_output_pattern: null,
    global_retry_attempts: 2,
    enable_directory_monitoring: false
  },
  activeServices: {
    htr_provider_id: "ollama_llava",
    formatting_provider_id: "anthropic_claude_haiku"
  },
  isLoading: false,
  isSaving: false,
  testing: {},
  testResults: {},
  error: null,
  success: null,
  showApiKeys: {}
}

// Action types
const ActionTypes = {
  SET_CONFIG: 'SET_CONFIG',
  SET_LOADING: 'SET_LOADING',
  SET_SAVING: 'SET_SAVING',
  UPDATE_PROVIDER_CONFIG: 'UPDATE_PROVIDER_CONFIG',
  UPDATE_APP_SETTINGS: 'UPDATE_APP_SETTINGS',
  UPDATE_ACTIVE_SERVICES: 'UPDATE_ACTIVE_SERVICES',
  SET_TESTING: 'SET_TESTING',
  SET_TEST_RESULTS: 'SET_TEST_RESULTS',
  SET_ERROR: 'SET_ERROR',
  SET_SUCCESS: 'SET_SUCCESS',
  TOGGLE_API_KEY_VISIBILITY: 'TOGGLE_API_KEY_VISIBILITY',
  CLEAR_MESSAGES: 'CLEAR_MESSAGES'
}

/**
 * Settings state reducer
 * @param {SettingsState} state - Current state
 * @param {Object} action - Action object with type and payload
 * @returns {SettingsState} New state
 */
function settingsReducer(state, action) {
  switch (action.type) {
    case ActionTypes.SET_CONFIG:
      return {
        ...state,
        config: action.payload,
        aiProviders: action.payload?.ai_provider_configs || {},
        appSettings: action.payload?.app_settings || state.appSettings,
        activeServices: action.payload?.active_services || state.activeServices
      }

    case ActionTypes.SET_LOADING:
      return {
        ...state,
        isLoading: action.payload
      }

    case ActionTypes.SET_SAVING:
      return {
        ...state,
        isSaving: action.payload
      }

    case ActionTypes.UPDATE_PROVIDER_CONFIG: {
      const { providerId, updates } = action.payload
      const newProviders = {
        ...state.aiProviders,
        [providerId]: {
          ...state.aiProviders[providerId],
          ...updates
        }
      }
      return {
        ...state,
        aiProviders: newProviders,
        config: state.config ? {
          ...state.config,
          ai_provider_configs: newProviders
        } : null
      }
    }

    case ActionTypes.UPDATE_APP_SETTINGS: {
      const newAppSettings = {
        ...state.appSettings,
        ...action.payload
      }
      return {
        ...state,
        appSettings: newAppSettings,
        config: state.config ? {
          ...state.config,
          app_settings: newAppSettings
        } : null
      }
    }

    case ActionTypes.UPDATE_ACTIVE_SERVICES: {
      const newActiveServices = {
        ...state.activeServices,
        ...action.payload
      }
      return {
        ...state,
        activeServices: newActiveServices,
        config: state.config ? {
          ...state.config,
          active_services: newActiveServices
        } : null
      }
    }

    case ActionTypes.SET_TESTING:
      return {
        ...state,
        testing: {
          ...state.testing,
          ...action.payload
        }
      }

    case ActionTypes.SET_TEST_RESULTS:
      return {
        ...state,
        testResults: {
          ...state.testResults,
          ...action.payload
        }
      }

    case ActionTypes.SET_ERROR:
      return {
        ...state,
        error: action.payload,
        success: null
      }

    case ActionTypes.SET_SUCCESS:
      return {
        ...state,
        success: action.payload,
        error: null
      }

    case ActionTypes.TOGGLE_API_KEY_VISIBILITY:
      return {
        ...state,
        showApiKeys: {
          ...state.showApiKeys,
          [action.payload]: !state.showApiKeys[action.payload]
        }
      }

    case ActionTypes.CLEAR_MESSAGES:
      return {
        ...state,
        error: null,
        success: null
      }

    default:
      return state
  }
}

// Create context
const SettingsContext = createContext(null)

// Local storage keys
const SETTINGS_CACHE_KEY = 'ink2md_settings_cache'
const SETTINGS_CACHE_TIMESTAMP_KEY = 'ink2md_settings_cache_timestamp'
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

/**
 * Helper function to get backend URL
 * @returns {string} Backend URL
 */
function getBackendUrl() {
  const hostname = window.location.hostname
  const protocol = window.location.protocol

  if (hostname === 'localhost') {
    return 'http://localhost:6201'
  } else if (hostname.match(/^\d+\.\d+\.\d+\.\d+$/)) {
    return `${protocol}//${hostname}:6201`
  } else {
    return `${protocol}//${hostname}/api`
  }
}

/**
 * Flatten nested configuration object to dot notation
 * @param {Object} obj - Object to flatten
 * @param {string} prefix - Key prefix
 * @returns {Object} Flattened object
 */
function flattenConfig(obj, prefix = '') {
  const flattened = {}
  
  for (const [key, value] of Object.entries(obj)) {
    const newKey = prefix ? `${prefix}.${key}` : key
    
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      Object.assign(flattened, flattenConfig(value, newKey))
    } else {
      flattened[newKey] = value
    }
  }
  
  return flattened
}

/**
 * SettingsProvider component
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components
 * @returns {JSX.Element} Provider component
 */
export function SettingsProvider({ children }) {
  const [state, dispatch] = useReducer(settingsReducer, initialState)
  const isInitialMount = useRef(true)

  // Auto-clear messages after timeout
  useEffect(() => {
    if (state.error || state.success) {
      const timer = setTimeout(() => {
        dispatch({ type: ActionTypes.CLEAR_MESSAGES })
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [state.error, state.success])

  // Local storage helpers
  const saveToLocalStorage = useCallback((settings) => {
    try {
      localStorage.setItem(SETTINGS_CACHE_KEY, JSON.stringify(settings))
      localStorage.setItem(SETTINGS_CACHE_TIMESTAMP_KEY, Date.now().toString())
    } catch (err) {
      console.warn('Failed to save settings to localStorage:', err)
    }
  }, [])

  const loadFromLocalStorage = useCallback(() => {
    try {
      const cached = localStorage.getItem(SETTINGS_CACHE_KEY)
      const timestamp = localStorage.getItem(SETTINGS_CACHE_TIMESTAMP_KEY)
      
      if (cached && timestamp) {
        const age = Date.now() - parseInt(timestamp)
        if (age < CACHE_DURATION) {
          return JSON.parse(cached)
        }
      }
    } catch (err) {
      console.warn('Failed to load settings from localStorage:', err)
    }
    return null
  }, [])

  const clearLocalStorageCache = useCallback(() => {
    try {
      localStorage.removeItem(SETTINGS_CACHE_KEY)
      localStorage.removeItem(SETTINGS_CACHE_TIMESTAMP_KEY)
    } catch (err) {
      console.warn('Failed to clear localStorage cache:', err)
    }
  }, [])

  // Action creators
  const actions = {
    /**
     * Load configuration from backend
     */
    loadConfig: useCallback(async () => {
      try {
        dispatch({ type: ActionTypes.SET_LOADING, payload: true })
        dispatch({ type: ActionTypes.SET_ERROR, payload: null })

        // Try loading from cache first
        const cachedSettings = loadFromLocalStorage()
        if (cachedSettings) {
          dispatch({ type: ActionTypes.SET_CONFIG, payload: cachedSettings })
          dispatch({ type: ActionTypes.SET_LOADING, payload: false })
          return
        }

        // Load from backend
        const response = await fetch(`${getBackendUrl()}/api/config`)
        
        if (!response.ok) {
          throw new Error(`Failed to load configuration: ${response.status}`)
        }
        
        const data = await response.json()
        dispatch({ type: ActionTypes.SET_CONFIG, payload: data })
        saveToLocalStorage(data)
        
      } catch (err) {
        console.error('Error loading configuration:', err)
        dispatch({ type: ActionTypes.SET_ERROR, payload: `Failed to load configuration: ${err.message}` })
        
        // Fallback to cached settings
        const cachedSettings = loadFromLocalStorage()
        if (cachedSettings) {
          dispatch({ type: ActionTypes.SET_CONFIG, payload: cachedSettings })
        }
      } finally {
        dispatch({ type: ActionTypes.SET_LOADING, payload: false })
      }
    }, [loadFromLocalStorage, saveToLocalStorage]),

    /**
     * Save configuration to backend
     */
    saveConfig: useCallback(async () => {
      try {
        dispatch({ type: ActionTypes.SET_SAVING, payload: true })
        dispatch({ type: ActionTypes.SET_ERROR, payload: null })

        // Save to localStorage immediately
        saveToLocalStorage(state.config)

        // Flatten config for backend
        const flatConfig = flattenConfig(state.config)
        
        const response = await fetch(`${getBackendUrl()}/api/config`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(flatConfig),
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || `Config save failed: ${response.status}`)
        }

        const result = await response.json()
        dispatch({ type: ActionTypes.SET_CONFIG, payload: result.new_config })
        saveToLocalStorage(result.new_config)
        
        // Reload providers
        try {
          await fetch(`${getBackendUrl()}/api/providers/reload`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
          })
          dispatch({ type: ActionTypes.SET_SUCCESS, payload: 'Configuration saved and providers reloaded successfully!' })
        } catch (reloadErr) {
          dispatch({ type: ActionTypes.SET_SUCCESS, payload: 'Configuration saved successfully! (Provider reload failed - restart may be needed)' })
        }
        
      } catch (err) {
        console.error('Error saving configuration:', err)
        dispatch({ type: ActionTypes.SET_ERROR, payload: `Failed to save configuration: ${err.message}` })
        clearLocalStorageCache()
      } finally {
        dispatch({ type: ActionTypes.SET_SAVING, payload: false })
      }
    }, [state.config, saveToLocalStorage, clearLocalStorageCache]),

    /**
     * Update AI provider configuration
     * @param {string} providerId - Provider ID
     * @param {Object} updates - Configuration updates
     */
    updateProviderConfig: useCallback((providerId, updates) => {
      dispatch({
        type: ActionTypes.UPDATE_PROVIDER_CONFIG,
        payload: { providerId, updates }
      })
    }, []),

    /**
     * Update application settings
     * @param {Object} updates - Settings updates
     */
    updateAppSettings: useCallback((updates) => {
      dispatch({ type: ActionTypes.UPDATE_APP_SETTINGS, payload: updates })
    }, []),

    /**
     * Update active services
     * @param {Object} updates - Service updates
     */
    updateActiveServices: useCallback((updates) => {
      dispatch({ type: ActionTypes.UPDATE_ACTIVE_SERVICES, payload: updates })
    }, []),

    /**
     * Test specific AI provider
     * @param {string} providerId - Provider ID to test
     */
    testProvider: useCallback(async (providerId) => {
      try {
        dispatch({ type: ActionTypes.SET_TESTING, payload: { [providerId]: true } })
        dispatch({ type: ActionTypes.SET_TEST_RESULTS, payload: { [providerId]: null } })
        
        const response = await fetch(`${getBackendUrl()}/api/providers/test`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ provider_id: providerId }),
        })

        if (!response.ok) {
          throw new Error(`Test failed: ${response.status}`)
        }

        const result = await response.json()
        dispatch({ type: ActionTypes.SET_TEST_RESULTS, payload: { [providerId]: result[providerId] } })
      } catch (err) {
        console.error(`Error testing provider ${providerId}:`, err)
        dispatch({ 
          type: ActionTypes.SET_TEST_RESULTS, 
          payload: { 
            [providerId]: { 
              success: false, 
              message: err.message 
            } 
          }
        })
      } finally {
        dispatch({ type: ActionTypes.SET_TESTING, payload: { [providerId]: false } })
      }
    }, []),

    /**
     * Test all AI providers
     */
    testAllProviders: useCallback(async () => {
      try {
        const providerIds = Object.keys(state.aiProviders)
        const testingState = Object.fromEntries(providerIds.map(id => [id, true]))
        
        dispatch({ type: ActionTypes.SET_TESTING, payload: testingState })
        dispatch({ type: ActionTypes.SET_TEST_RESULTS, payload: {} })
        
        const response = await fetch(`${getBackendUrl()}/api/providers/test`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({}),
        })

        if (!response.ok) {
          throw new Error(`Test failed: ${response.status}`)
        }

        const results = await response.json()
        dispatch({ type: ActionTypes.SET_TEST_RESULTS, payload: results })
      } catch (err) {
        console.error('Error testing all providers:', err)
        dispatch({ type: ActionTypes.SET_ERROR, payload: `Failed to test providers: ${err.message}` })
      } finally {
        dispatch({ type: ActionTypes.SET_TESTING, payload: {} })
      }
    }, [state.aiProviders]),

    /**
     * Toggle API key visibility
     * @param {string} providerId - Provider ID
     */
    toggleApiKeyVisibility: useCallback((providerId) => {
      dispatch({ type: ActionTypes.TOGGLE_API_KEY_VISIBILITY, payload: providerId })
    }, []),

    /**
     * Reset all settings to defaults
     */
    resetToDefaults: useCallback(() => {
      if (window.confirm('Are you sure you want to reset all settings to defaults? This action cannot be undone.')) {
        const defaultConfig = {
          app_settings: {
            monitored_input_dir: "/app/input_pdfs",
            processed_output_dir: "/app/output_markdown",
            default_output_pattern: "YYYY-MM-DD-[OriginalFileName].md",
            custom_output_pattern: null,
            global_retry_attempts: 2,
            enable_directory_monitoring: false
          },
          active_services: {
            htr_provider_id: "ollama_llava",
            formatting_provider_id: "anthropic_claude_haiku"
          },
          ai_provider_configs: {
            ollama_llava: {
              display_name: "Ollama (LLaVA for HTR)",
              type: "ollama",
              api_base_url: "http://ollama:11434",
              model: "llava",
              is_htr_capable: true,
              is_formatting_capable: false,
              enabled: true
            },
            anthropic_claude_haiku: {
              display_name: "Anthropic (Claude 3 Haiku)",
              type: "anthropic",
              api_key: "${ANTHROPIC_API_KEY}",
              model: "claude-3-haiku-20240307",
              is_htr_capable: true,
              is_formatting_capable: true,
              is_vlm_capable: true,
              enabled: true
            }
          }
        }
        
        dispatch({ type: ActionTypes.SET_CONFIG, payload: defaultConfig })
        clearLocalStorageCache()
      }
    }, [clearLocalStorageCache]),

    /**
     * Clear error message
     */
    clearError: useCallback(() => {
      dispatch({ type: ActionTypes.SET_ERROR, payload: null })
    }, []),

    /**
     * Clear success message
     */
    clearSuccess: useCallback(() => {
      dispatch({ type: ActionTypes.SET_SUCCESS, payload: null })
    }, [])
  }

  const contextValue = {
    ...state,
    ...actions
  }

  return (
    <SettingsContext.Provider value={contextValue}>
      {children}
    </SettingsContext.Provider>
  )
}

/**
 * Custom hook to use settings context
 * @returns {SettingsState & SettingsActions} Settings state and actions
 * @throws {Error} If used outside of SettingsProvider
 */
export function useSettings() {
  const context = useContext(SettingsContext)
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider')
  }
  return context
}

export default SettingsContext