import { useState, useEffect } from 'react'
import './Settings.css'

const Settings = ({ isOpen, onClose }) => {
  const [config, setConfig] = useState(null)
  const [prompts, setPrompts] = useState({ templates: [], categories: [] })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState({})
  const [testResults, setTestResults] = useState({})
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [showApiKeys, setShowApiKeys] = useState({})
  const [activeTab, setActiveTab] = useState('providers')
  const [promptsLoading, setPromptsLoading] = useState(false)
  const [selectedPrompt, setSelectedPrompt] = useState(null)
  const [promptFilter, setPromptFilter] = useState('all')
  const [editingPrompt, setEditingPrompt] = useState(null)

  // Helper function to get the backend URL
  const getBackendUrl = () => {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;

    if (hostname === 'localhost') {
      return 'http://localhost:6201';
    } else if (hostname.match(/^\d+\.\d+\.\d+\.\d+$/)) {
      return `${protocol}//${hostname}:6201`;
    } else {
      return `${protocol}//${hostname}/api`;
    }
  };

  // Load configuration and prompts on component mount
  useEffect(() => {
    if (isOpen) {
      loadConfigWithCache()
      if (activeTab === 'prompts') {
        loadPrompts()
      }
    }
  }, [isOpen, activeTab])

  // Settings persistence functions
  const SETTINGS_CACHE_KEY = 'ink2md_settings_cache'
  const SETTINGS_CACHE_TIMESTAMP_KEY = 'ink2md_settings_cache_timestamp'
  const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

  const saveToLocalStorage = (settings) => {
    try {
      localStorage.setItem(SETTINGS_CACHE_KEY, JSON.stringify(settings))
      localStorage.setItem(SETTINGS_CACHE_TIMESTAMP_KEY, Date.now().toString())
    } catch (err) {
      console.warn('Failed to save settings to localStorage:', err)
    }
  }

  const loadFromLocalStorage = () => {
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
  }

  const clearLocalStorageCache = () => {
    try {
      localStorage.removeItem(SETTINGS_CACHE_KEY)
      localStorage.removeItem(SETTINGS_CACHE_TIMESTAMP_KEY)
    } catch (err) {
      console.warn('Failed to clear localStorage cache:', err)
    }
  }

  const syncSettingsToBackend = async (settings) => {
    try {
      const response = await fetch(`${getBackendUrl()}/api/user-settings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ settings }),
      })

      if (!response.ok) {
        throw new Error(`Failed to sync settings: ${response.status}`)
      }

      const result = await response.json()
      console.log('Settings synced to backend:', result)
      return true
    } catch (err) {
      console.error('Failed to sync settings to backend:', err)
      return false
    }
  }

  const loadUserSettingsFromBackend = async () => {
    try {
      const response = await fetch(`${getBackendUrl()}/api/user-settings`)
      
      if (!response.ok) {
        throw new Error(`Failed to load user settings: ${response.status}`)
      }
      
      const data = await response.json()
      return data.settings || {}
    } catch (err) {
      console.error('Failed to load user settings from backend:', err)
      return {}
    }
  }

  const loadConfigWithCache = async () => {
    try {
      setLoading(true)
      setError(null)

      // Priority: localStorage → backend → defaults
      let cachedSettings = loadFromLocalStorage()
      
      if (cachedSettings) {
        console.log('Loading settings from localStorage cache')
        setConfig(cachedSettings)
        setLoading(false)
        
        // Load from backend in background to sync
        loadUserSettingsFromBackend().then(backendSettings => {
          if (Object.keys(backendSettings).length > 0) {
            // Merge backend settings with cached settings
            const mergedConfig = mergeSettingsWithConfig(cachedSettings, backendSettings)
            setConfig(mergedConfig)
            saveToLocalStorage(mergedConfig)
          }
        })
        return
      }

      // Load from backend
      const [configResponse, userSettings] = await Promise.all([
        fetch(`${getBackendUrl()}/api/config`),
        loadUserSettingsFromBackend()
      ])
      
      if (!configResponse.ok) {
        throw new Error(`Failed to load configuration: ${configResponse.status}`)
      }
      
      const configData = await configResponse.json()
      
      // Merge user settings with config
      const mergedConfig = mergeSettingsWithConfig(configData, userSettings)
      
      setConfig(mergedConfig)
      saveToLocalStorage(mergedConfig)
      
    } catch (err) {
      console.error('Error loading configuration:', err)
      setError(`Failed to load configuration: ${err.message}`)
      
      // Fallback to cached settings if available
      const cachedSettings = loadFromLocalStorage()
      if (cachedSettings) {
        console.log('Falling back to cached settings')
        setConfig(cachedSettings)
      }
    } finally {
      setLoading(false)
    }
  }

  const mergeSettingsWithConfig = (config, userSettings) => {
    const merged = JSON.parse(JSON.stringify(config)) // Deep clone
    
    // Apply user settings to config
    for (const [key, setting] of Object.entries(userSettings)) {
      if (key.startsWith('ai_provider_configs.')) {
        const keys = key.split('.')
        let current = merged
        for (let i = 0; i < keys.length - 1; i++) {
          if (!current[keys[i]]) current[keys[i]] = {}
          current = current[keys[i]]
        }
        current[keys[keys.length - 1]] = setting.value
      }
    }
    
    return merged
  }

  const loadConfig = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch(`${getBackendUrl()}/api/config`)
      
      if (!response.ok) {
        throw new Error(`Failed to load configuration: ${response.status}`)
      }
      
      const data = await response.json()
      setConfig(data)
    } catch (err) {
      console.error('Error loading configuration:', err)
      setError(`Failed to load configuration: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const saveConfig = async () => {
    try {
      setSaving(true)
      setError(null)
      setSuccess(null)

      // Save to localStorage immediately for instant feedback
      saveToLocalStorage(config)

      // Convert nested config to dot-notation for backend
      const flatConfig = flattenConfig(config)
      
      // Save to traditional config endpoint
      const configResponse = await fetch(`${getBackendUrl()}/api/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(flatConfig),
      })

      if (!configResponse.ok) {
        const errorData = await configResponse.json()
        throw new Error(errorData.error || `Config save failed: ${configResponse.status}`)
      }

      const configResult = await configResponse.json()
      
      // Extract AI provider settings for user settings storage
      const aiProviderSettings = {}
      for (const [key, value] of Object.entries(flatConfig)) {
        if (key.startsWith('ai_provider_configs.')) {
          aiProviderSettings[key] = { value, type: typeof value === 'object' ? 'json' : 'string' }
        }
      }

      // Save AI provider settings to user settings for persistence
      if (Object.keys(aiProviderSettings).length > 0) {
        try {
          await syncSettingsToBackend(aiProviderSettings)
        } catch (syncErr) {
          console.warn('Failed to sync AI provider settings to user settings:', syncErr)
        }
      }
      
      // Update config with result
      setConfig(configResult.new_config)
      saveToLocalStorage(configResult.new_config)
      
      // Reload AI providers to pick up new configuration
      try {
        const reloadResponse = await fetch(`${getBackendUrl()}/api/providers/reload`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        })
        
        if (reloadResponse.ok) {
          setSuccess('Configuration saved and providers reloaded successfully!')
        } else {
          setSuccess('Configuration saved successfully! (Provider reload failed - restart may be needed)')
        }
      } catch (reloadErr) {
        console.warn('Failed to reload providers after config save:', reloadErr)
        setSuccess('Configuration saved successfully! (Provider reload failed - restart may be needed)')
      }
      
      // Clear success message and close modal after 2 seconds
      setTimeout(() => {
        setSuccess(null)
        onClose() // Close the settings modal
      }, 2000)
    } catch (err) {
      console.error('Error saving configuration:', err)
      setError(`Failed to save configuration: ${err.message}`)
      
      // Clear localStorage cache on save error
      clearLocalStorageCache()
    } finally {
      setSaving(false)
    }
  }

  const testProvider = async (providerId) => {
    try {
      setTesting(prev => ({ ...prev, [providerId]: true }))
      setTestResults(prev => ({ ...prev, [providerId]: null }))
      
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
      setTestResults(prev => ({ ...prev, [providerId]: result[providerId] }))
    } catch (err) {
      console.error(`Error testing provider ${providerId}:`, err)
      setTestResults(prev => ({ 
        ...prev, 
        [providerId]: { 
          success: false, 
          message: err.message 
        } 
      }))
    } finally {
      setTesting(prev => ({ ...prev, [providerId]: false }))
    }
  }

  const testAllProviders = async () => {
    try {
      const providerIds = Object.keys(config?.ai_provider_configs || {})
      setTesting(Object.fromEntries(providerIds.map(id => [id, true])))
      setTestResults({})
      
      const response = await fetch(`${getBackendUrl()}/api/providers/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}), // Empty body tests all providers
      })

      if (!response.ok) {
        throw new Error(`Test failed: ${response.status}`)
      }

      const results = await response.json()
      setTestResults(results)
    } catch (err) {
      console.error('Error testing all providers:', err)
      setError(`Failed to test providers: ${err.message}`)
    } finally {
      setTesting({})
    }
  }

  const loadPrompts = async () => {
    try {
      setPromptsLoading(true)
      setError(null)
      const response = await fetch(`${getBackendUrl()}/api/prompts`)
      
      if (!response.ok) {
        throw new Error(`Failed to load prompts: ${response.status}`)
      }
      
      const data = await response.json()
      setPrompts(data)
    } catch (err) {
      console.error('Error loading prompts:', err)
      setError(`Failed to load prompts: ${err.message}`)
    } finally {
      setPromptsLoading(false)
    }
  }

  const savePrompt = async (promptData) => {
    try {
      const method = editingPrompt ? 'PUT' : 'POST'
      const url = editingPrompt
        ? `${getBackendUrl()}/api/prompts/${editingPrompt.name}`
        : `${getBackendUrl()}/api/prompts`
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(promptData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `Save failed: ${response.status}`)
      }

      await loadPrompts()
      setEditingPrompt(null)
      setSuccess(editingPrompt ? 'Prompt updated successfully!' : 'Prompt created successfully!')
      
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      console.error('Error saving prompt:', err)
      setError(`Failed to save prompt: ${err.message}`)
    }
  }

  const deletePrompt = async (promptName) => {
    if (!window.confirm(`Are you sure you want to delete the prompt "${promptName}"?`)) {
      return
    }

    try {
      const response = await fetch(`${getBackendUrl()}/api/prompts/${promptName}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `Delete failed: ${response.status}`)
      }

      await loadPrompts()
      setSelectedPrompt(null)
      setSuccess('Prompt deleted successfully!')
      
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      console.error('Error deleting prompt:', err)
      setError(`Failed to delete prompt: ${err.message}`)
    }
  }

  const resetToDefaults = () => {
    if (window.confirm('Are you sure you want to reset all settings to defaults? This action cannot be undone.')) {
      // Reset to default configuration structure
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
          ollama_mistral: {
            display_name: "Ollama (Mistral for Formatting)",
            type: "ollama",
            api_base_url: "http://ollama:11434",
            model: "mistral",
            is_htr_capable: false,
            is_formatting_capable: true,
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
          },
          anthropic_claude_sonnet: {
            display_name: "Anthropic (Claude 3.5 Sonnet)",
            type: "anthropic",
            api_key: "${ANTHROPIC_API_KEY}",
            model: "claude-3-5-sonnet-20241022",
            is_htr_capable: true,
            is_formatting_capable: true,
            is_vlm_capable: true,
            enabled: true
          },
          anthropic_claude_opus: {
            display_name: "Anthropic (Claude 3 Opus)",
            type: "anthropic",
            api_key: "${ANTHROPIC_API_KEY}",
            model: "claude-3-opus-20240229",
            is_htr_capable: true,
            is_formatting_capable: true,
            is_vlm_capable: true,
            enabled: true
          }
        }
      }
      setConfig(defaultConfig)
      setTestResults({})
      
      // Clear localStorage cache when resetting to defaults
      clearLocalStorageCache()
    }
  }

  // Helper function to flatten nested config for backend
  const flattenConfig = (obj, prefix = '') => {
    const flattened = {}
    
    for (const key in obj) {
      const value = obj[key]
      const newKey = prefix ? `${prefix}.${key}` : key
      
      if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
        Object.assign(flattened, flattenConfig(value, newKey))
      } else {
        flattened[newKey] = value
      }
    }
    
    return flattened
  }

  const updateConfigValue = (path, value) => {
    const keys = path.split('.')
    const newConfig = JSON.parse(JSON.stringify(config)) // Deep clone
    
    let current = newConfig
    for (let i = 0; i < keys.length - 1; i++) {
      current = current[keys[i]]
    }
    current[keys[keys.length - 1]] = value
    
    setConfig(newConfig)
    
    // Save to localStorage immediately for instant persistence
    saveToLocalStorage(newConfig)
    
    // For AI provider settings, also sync to backend in background
    if (path.startsWith('ai_provider_configs.')) {
      const settingData = { [path]: { value, type: typeof value === 'object' ? 'json' : 'string' } }
      syncSettingsToBackend(settingData).catch(err => {
        console.warn('Failed to sync setting to backend:', err)
      })
    }
  }

  const toggleApiKeyVisibility = (providerId) => {
    setShowApiKeys(prev => ({
      ...prev,
      [providerId]: !prev[providerId]
    }))
  }

  if (!isOpen) return null

  return (
    <div className="settings-overlay">
      <div className="settings-modal">
        <div className="settings-header">
          <h2>Settings</h2>
          <button className="close-btn" onClick={onClose}>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="settings-content">
          {loading && (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Loading configuration...</p>
            </div>
          )}

          {error && (
            <div className="error-message">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
              </svg>
              {error}
            </div>
          )}

          {success && (
            <div className="success-message">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
              {success}
            </div>
          )}

          {/* Tab Navigation */}
          <div className="settings-tabs">
            <button
              className={`tab-btn ${activeTab === 'providers' ? 'active' : ''}`}
              onClick={() => setActiveTab('providers')}
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              AI Providers
            </button>
            <button
              className={`tab-btn ${activeTab === 'prompts' ? 'active' : ''}`}
              onClick={() => setActiveTab('prompts')}
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
              Prompts
            </button>
            <button
              className={`tab-btn ${activeTab === 'app' ? 'active' : ''}`}
              onClick={() => setActiveTab('app')}
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.343 3.94c.09-.542.56-.94 1.11-.94h1.093c.55 0 1.02.398 1.11.94l.149.894c.07.424.384.764.78.93.398.164.855.142 1.205-.108l.737-.527a1.125 1.125 0 011.45.12l.773.774c.39.389.44 1.002.12 1.45l-.527.737c-.25.35-.272.806-.107 1.204.165.397.505.71.93.78l.893.15c.543.09.94.56.94 1.109v1.094c0 .55-.397 1.02-.94 1.11l-.893.149c-.425.07-.765.383-.93.78-.165.398-.143.854.107 1.204l.527.738c.32.447.269 1.06-.12 1.45l-.774.773a1.125 1.125 0 01-1.449.12l-.738-.527c-.35-.25-.806-.272-1.203-.107-.397.165-.71.505-.781.929l-.149.894c-.09.542-.56.94-1.11.94h-1.094c-.55 0-1.019-.398-1.11-.94l-.148-.894c-.071-.424-.384-.764-.781-.93-.398-.164-.854-.142-1.204.108l-.738.527c-.447.32-1.06.269-1.45-.12l-.773-.774a1.125 1.125 0 01-.12-1.45l.527-.737c.25-.35.273-.806.108-1.204-.165-.397-.505-.71-.93-.78l-.894-.15c-.542-.09-.94-.56-.94-1.109v-1.094c0-.55.398-1.02.94-1.11l.894-.149c.424-.07.765-.383.93-.78.165-.398.143-.854-.107-1.204l-.527-.738a1.125 1.125 0 01.12-1.45l.773-.773a1.125 1.125 0 011.45-.12l.737.527c.35.25.807.272 1.204.107.397-.165.71-.505.78-.929l.15-.894z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Application
            </button>
          </div>

          {/* Tab Content */}
          {config && !loading && activeTab === 'providers' && (
            <>
              {/* AI Provider Configurations */}
              <div className="settings-section">
                <div className="section-header">
                  <h3>AI Provider Settings</h3>
                  <button 
                    className="test-all-btn"
                    onClick={testAllProviders}
                    disabled={Object.values(testing).some(Boolean)}
                  >
                    {Object.values(testing).some(Boolean) ? (
                      <>
                        <div className="spinner small"></div>
                        Testing...
                      </>
                    ) : (
                      <>
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5.636 5.636a9 9 0 1 0 12.728 0M12 3v9" />
                        </svg>
                        Test All
                      </>
                    )}
                  </button>
                </div>

                {Object.entries(config.ai_provider_configs || {}).map(([providerId, provider]) => (
                  <div key={providerId} className="provider-config">
                    <div className="provider-header">
                      <div className="provider-info">
                        <h4>{provider.display_name}</h4>
                        <span className={`provider-type ${provider.type}`}>{provider.type}</span>
                        <span className={`provider-status ${provider.enabled ? 'enabled' : 'disabled'}`}>
                          {provider.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                      </div>
                      <div className="provider-actions">
                        <button
                          className="test-btn"
                          onClick={() => testProvider(providerId)}
                          disabled={testing[providerId]}
                        >
                          {testing[providerId] ? (
                            <div className="spinner small"></div>
                          ) : (
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M5.636 5.636a9 9 0 1 0 12.728 0M12 3v9" />
                            </svg>
                          )}
                          Test
                        </button>
                      </div>
                    </div>

                    {testResults[providerId] && (
                      <div className={`test-result ${testResults[providerId].success ? 'success' : 'error'}`}>
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                          {testResults[providerId].success ? (
                            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                          ) : (
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
                          )}
                        </svg>
                        {testResults[providerId].message}
                      </div>
                    )}

                    <div className="provider-fields">
                      <div className="field-group">
                        <label>Enabled</label>
                        <input
                          type="checkbox"
                          checked={provider.enabled}
                          onChange={(e) => updateConfigValue(`ai_provider_configs.${providerId}.enabled`, e.target.checked)}
                        />
                      </div>

                      {provider.type === 'anthropic' && (
                        <div className="field-group">
                          <label>API Key</label>
                          <div className="api-key-input">
                            <input
                              type={showApiKeys[providerId] ? "text" : "password"}
                              value={provider.api_key || ''}
                              onChange={(e) => updateConfigValue(`ai_provider_configs.${providerId}.api_key`, e.target.value)}
                              placeholder="Enter Anthropic API key"
                            />
                            <button
                              type="button"
                              className="toggle-visibility"
                              onClick={() => toggleApiKeyVisibility(providerId)}
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                                {showApiKeys[providerId] ? (
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 1-4.243-4.243m4.242 4.242L9.88 9.88" />
                                ) : (
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
                                )}
                              </svg>
                            </button>
                          </div>
                        </div>
                      )}

                      {provider.type === 'ollama' && (
                        <div className="field-group">
                          <label>API Base URL</label>
                          <input
                            type="text"
                            value={provider.api_base_url || ''}
                            onChange={(e) => updateConfigValue(`ai_provider_configs.${providerId}.api_base_url`, e.target.value)}
                            placeholder="http://ollama:11434"
                          />
                        </div>
                      )}

                      <div className="field-group">
                        <label>Model</label>
                        <input
                          type="text"
                          value={provider.model || ''}
                          onChange={(e) => updateConfigValue(`ai_provider_configs.${providerId}.model`, e.target.value)}
                          placeholder="Model name"
                        />
                      </div>

                      <div className="capabilities">
                        <div className="field-group">
                          <label>HTR Capable</label>
                          <input
                            type="checkbox"
                            checked={provider.is_htr_capable}
                            onChange={(e) => updateConfigValue(`ai_provider_configs.${providerId}.is_htr_capable`, e.target.checked)}
                          />
                        </div>
                        <div className="field-group">
                          <label>Formatting Capable</label>
                          <input
                            type="checkbox"
                            checked={provider.is_formatting_capable}
                            onChange={(e) => updateConfigValue(`ai_provider_configs.${providerId}.is_formatting_capable`, e.target.checked)}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Active Services */}
              <div className="settings-section">
                <h3>Active Services</h3>
                <div className="service-selection-info">
                  <p>Configure different AI models for specific tasks. Vision models excel at HTR (Handwritten Text Recognition), while text models are optimized for formatting and processing.</p>
                </div>
                <div className="active-services">
                  <div className="service-group">
                    <h4>Vision Processing (HTR)</h4>
                    <div className="field-group">
                      <label>HTR Provider (Vision)</label>
                      <select
                        value={config.active_services?.htr_provider_id || ''}
                        onChange={(e) => updateConfigValue('active_services.htr_provider_id', e.target.value)}
                      >
                        <option value="">Select HTR Provider</option>
                        {Object.entries(config.ai_provider_configs || {})
                          .filter(([_, provider]) => provider.is_htr_capable && provider.enabled)
                          .map(([id, provider]) => (
                            <option key={id} value={id}>
                              {provider.display_name} ({provider.model})
                            </option>
                          ))}
                      </select>
                    </div>
                  </div>
                  
                  <div className="service-group">
                    <h4>Text Processing</h4>
                    <div className="field-group">
                      <label>Formatting Provider (Text)</label>
                      <select
                        value={config.active_services?.formatting_provider_id || ''}
                        onChange={(e) => updateConfigValue('active_services.formatting_provider_id', e.target.value)}
                      >
                        <option value="">Select Formatting Provider</option>
                        {Object.entries(config.ai_provider_configs || {})
                          .filter(([_, provider]) => provider.is_formatting_capable && provider.enabled)
                          .map(([id, provider]) => (
                            <option key={id} value={id}>
                              {provider.display_name} ({provider.model})
                            </option>
                          ))}
                      </select>
                    </div>
                  </div>

                  <div className="service-group">
                    <h4>Direct Vision-to-Markdown (VLM)</h4>
                    <div className="field-group">
                      <label>VLM Provider (Optional)</label>
                      <select
                        value={config.active_services?.vlm_provider_id || ''}
                        onChange={(e) => updateConfigValue('active_services.vlm_provider_id', e.target.value)}
                      >
                        <option value="">Select VLM Provider (Optional)</option>
                        {Object.entries(config.ai_provider_configs || {})
                          .filter(([_, provider]) => provider.is_vlm_capable && provider.enabled)
                          .map(([id, provider]) => (
                            <option key={id} value={id}>
                              {provider.display_name} ({provider.model})
                            </option>
                          ))}
                      </select>
                    </div>
                  </div>
                </div>

                {/* Model Recommendations */}
                <div className="model-recommendations">
                  <h4>Model Recommendations</h4>
                  
                  {/* Anthropic (Cloud) Models */}
                  <h5 style={{marginTop: '0', marginBottom: '12px', color: '#a855f7', fontSize: '1rem'}}>Anthropic (Cloud)</h5>
                  <div className="recommendation-grid">
                    <div className="recommendation-item">
                      <h5>Claude 3.5 Sonnet (New) ⭐ RECOMMENDED</h5>
                      <p><strong>Model:</strong> <code>claude-3-5-sonnet-20241022</code></p>
                      <p><strong>Best for:</strong> document analysis, handwriting recognition, complex layouts</p>
                      <span className="recommendation-note">Cost: medium, Speed: fast</span>
                    </div>
                    <div className="recommendation-item">
                      <h5>Claude 3 Opus</h5>
                      <p><strong>Model:</strong> <code>claude-3-opus-20240229</code></p>
                      <p><strong>Best for:</strong> complex visual reasoning, detailed document analysis</p>
                      <span className="recommendation-note">Cost: high, Speed: medium</span>
                    </div>
                    <div className="recommendation-item">
                      <h5>Claude 3 Haiku</h5>
                      <p><strong>Model:</strong> <code>claude-3-haiku-20240307</code></p>
                      <p><strong>Best for:</strong> simple OCR, high-volume processing</p>
                      <span className="recommendation-note">Cost: low, Speed: very fast</span>
                    </div>
                  </div>

                  {/* Ollama (Local) Models */}
                  <h5 style={{marginTop: '24px', marginBottom: '12px', color: '#a855f7', fontSize: '1rem'}}>Ollama (Local)</h5>
                  <div className="recommendation-grid">
                    <div className="recommendation-item">
                      <h5>LLaVA 1.6 (13B) ⭐ RECOMMENDED</h5>
                      <p><strong>Model:</strong> <code>llava:13b</code></p>
                      <p><strong>Best for:</strong> document analysis, handwriting, general vision</p>
                      <span className="recommendation-note">Memory: 16GB+, Speed: medium</span>
                    </div>
                    <div className="recommendation-item">
                      <h5>LLaVA 1.6 (7B)</h5>
                      <p><strong>Model:</strong> <code>llava:7b</code></p>
                      <p><strong>Best for:</strong> basic OCR, simple vision tasks</p>
                      <span className="recommendation-note">Memory: 8GB+, Speed: fast</span>
                    </div>
                    <div className="recommendation-item">
                      <h5>Bakllava (7B)</h5>
                      <p><strong>Model:</strong> <code>bakllava:7b</code></p>
                      <p><strong>Best for:</strong> OCR capabilities, document processing</p>
                      <span className="recommendation-note">Memory: 8GB+, Speed: fast</span>
                    </div>
                    <div className="recommendation-item">
                      <h5>Moondream 2 (7B)</h5>
                      <p><strong>Model:</strong> <code>moondream:7b</code></p>
                      <p><strong>Best for:</strong> image description and analysis</p>
                      <span className="recommendation-note">Memory: 8GB+, Speed: fast</span>
                    </div>
                    <div className="recommendation-item">
                      <h5>LLaVA-Phi (7B)</h5>
                      <p><strong>Model:</strong> <code>llava-phi:7b</code></p>
                      <p><strong>Best for:</strong> vision-language performance</p>
                      <span className="recommendation-note">Memory: 8GB+, Speed: fast</span>
                    </div>
                    <div className="recommendation-item">
                      <h5>Dolphin-Vision (7B)</h5>
                      <p><strong>Model:</strong> <code>dolphin-vision:7b</code></p>
                      <p><strong>Best for:</strong> visual reasoning, complex visual tasks</p>
                      <span className="recommendation-note">Memory: 8GB+, Speed: fast</span>
                    </div>
                    <div className="recommendation-item">
                      <h5>Nous-Hermes-Vision (13B)</h5>
                      <p><strong>Model:</strong> <code>nous-hermes2-vision:13b</code></p>
                      <p><strong>Best for:</strong> document analysis, strong reasoning</p>
                      <span className="recommendation-note">Memory: 16GB+, Speed: medium</span>
                    </div>
                  </div>
                </div>
              </div>

            </>
          )}

          {/* Prompts Tab */}
          {activeTab === 'prompts' && (
            <div className="prompts-tab">
              {promptsLoading && (
                <div className="loading-state">
                  <div className="spinner"></div>
                  <p>Loading prompts...</p>
                </div>
              )}

              {!promptsLoading && (
                <>
                  <div className="prompts-header">
                    <div className="prompts-controls">
                      <select
                        value={promptFilter}
                        onChange={(e) => setPromptFilter(e.target.value)}
                        className="prompt-filter"
                      >
                        <option value="all">All Categories</option>
                        {prompts.categories.map(category => (
                          <option key={category} value={category}>
                            {category.charAt(0).toUpperCase() + category.slice(1)}
                          </option>
                        ))}
                      </select>
                      <button
                        className="new-prompt-btn"
                        onClick={() => setEditingPrompt({ name: '', content: '', description: '', category: 'custom' })}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                        </svg>
                        New Prompt
                      </button>
                    </div>
                  </div>

                  <div className="prompts-content">
                    <div className="prompts-list">
                      {prompts.templates
                        .filter(template => promptFilter === 'all' || template.category === promptFilter)
                        .map(template => (
                          <div
                            key={template.name}
                            className={`prompt-item ${selectedPrompt?.name === template.name ? 'selected' : ''}`}
                            onClick={() => setSelectedPrompt(template)}
                          >
                            <div className="prompt-header">
                              <h4>{template.name}</h4>
                              <span className={`prompt-category ${template.category}`}>
                                {template.category}
                              </span>
                            </div>
                            <p className="prompt-description">{template.description}</p>
                            {template.variables.length > 0 && (
                              <div className="prompt-variables">
                                Variables: {template.variables.join(', ')}
                              </div>
                            )}
                          </div>
                        ))}
                    </div>

                    {selectedPrompt && (
                      <div className="prompt-details">
                        <div className="prompt-details-header">
                          <h3>{selectedPrompt.name}</h3>
                          <div className="prompt-actions">
                            {selectedPrompt.is_custom && (
                              <>
                                <button
                                  className="edit-btn"
                                  onClick={() => setEditingPrompt(selectedPrompt)}
                                >
                                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                                  </svg>
                                  Edit
                                </button>
                                <button
                                  className="delete-btn"
                                  onClick={() => deletePrompt(selectedPrompt.name)}
                                >
                                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                                  </svg>
                                  Delete
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                        <div className="prompt-content">
                          <pre>{selectedPrompt.content}</pre>
                        </div>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          )}

          {/* Application Settings Tab */}
          {config && !loading && activeTab === 'app' && (
            <div className="settings-section">
              <h3>Application Settings</h3>
              <div className="app-settings">
                <div className="field-group">
                  <label>Output Pattern</label>
                  <input
                    type="text"
                    value={config.app_settings?.default_output_pattern || ''}
                    onChange={(e) => updateConfigValue('app_settings.default_output_pattern', e.target.value)}
                    placeholder="YYYY-MM-DD-[OriginalFileName].md"
                  />
                </div>
                <div className="field-group">
                  <label>Retry Attempts</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={config.app_settings?.global_retry_attempts || 0}
                    onChange={(e) => updateConfigValue('app_settings.global_retry_attempts', parseInt(e.target.value))}
                  />
                </div>
                <div className="field-group">
                  <label>Directory Monitoring</label>
                  <input
                    type="checkbox"
                    checked={config.app_settings?.enable_directory_monitoring || false}
                    onChange={(e) => updateConfigValue('app_settings.enable_directory_monitoring', e.target.checked)}
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="settings-footer">
          <button className="reset-btn" onClick={resetToDefaults} disabled={loading || saving}>
            Reset to Defaults
          </button>
          <div className="footer-actions">
            <button className="cancel-btn" onClick={onClose} disabled={saving}>
              Cancel
            </button>
            <button 
              className="save-btn" 
              onClick={saveConfig} 
              disabled={loading || saving || !config}
            >
              {saving ? (
                <>
                  <div className="spinner small"></div>
                  Saving...
                </>
              ) : (
                'Save Changes'
              )}
            </button>
          </div>
        </div>

        {/* Prompt Editor Modal */}
        {editingPrompt && (
          <div className="prompt-editor-overlay">
            <div className="prompt-editor-modal">
              <div className="prompt-editor-header">
                <h3>{editingPrompt.name ? 'Edit Prompt' : 'New Prompt'}</h3>
                <button
                  className="close-btn"
                  onClick={() => setEditingPrompt(null)}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <div className="prompt-editor-content">
                <div className="prompt-editor-fields">
                  <div className="field-group">
                    <label>Name</label>
                    <input
                      type="text"
                      value={editingPrompt.name || ''}
                      onChange={(e) => setEditingPrompt({...editingPrompt, name: e.target.value})}
                      placeholder="Enter prompt name"
                      disabled={!!selectedPrompt && !selectedPrompt.is_custom}
                    />
                  </div>
                  
                  <div className="field-group">
                    <label>Description</label>
                    <input
                      type="text"
                      value={editingPrompt.description || ''}
                      onChange={(e) => setEditingPrompt({...editingPrompt, description: e.target.value})}
                      placeholder="Enter prompt description"
                    />
                  </div>
                  
                  <div className="field-group">
                    <label>Category</label>
                    <select
                      value={editingPrompt.category || 'custom'}
                      onChange={(e) => setEditingPrompt({...editingPrompt, category: e.target.value})}
                    >
                      <option value="custom">Custom</option>
                      <option value="htr">HTR</option>
                      <option value="formatting">Formatting</option>
                      <option value="vlm">VLM</option>
                    </select>
                  </div>
                  
                  <div className="field-group">
                    <label>Content</label>
                    <textarea
                      value={editingPrompt.content || ''}
                      onChange={(e) => setEditingPrompt({...editingPrompt, content: e.target.value})}
                      placeholder="Enter prompt content..."
                      rows={12}
                    />
                  </div>
                </div>
              </div>
              
              <div className="prompt-editor-footer">
                <button
                  className="cancel-btn"
                  onClick={() => setEditingPrompt(null)}
                >
                  Cancel
                </button>
                <button
                  className="save-btn"
                  onClick={() => savePrompt(editingPrompt)}
                  disabled={!editingPrompt.name || !editingPrompt.content}
                >
                  {editingPrompt.name && selectedPrompt ? 'Update' : 'Create'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Settings