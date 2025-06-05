/**
 * @fileoverview useSettings hook - Custom hook for SettingsContext
 * 
 * Provides convenient access to application settings and configuration.
 * This hook wraps the SettingsContext and provides additional utility functions
 * for settings management, validation, and testing.
 * 
 * @author Sarah Wolff
 * @version 0.5 beta
 */

import { useSettings as useSettingsContext } from '../contexts/SettingsContext'

/**
 * Custom hook for accessing and managing application settings
 * 
 * @returns {Object} Settings state and utility functions
 * @throws {Error} If used outside of SettingsProvider
 * 
 * @example
 * ```jsx
 * function SettingsPanel() {
 *   const { 
 *     aiProviders,
 *     activeServices,
 *     updateProvider,
 *     testProvider,
 *     isProviderEnabled,
 *     getProviderStatus
 *   } = useSettings()
 *   
 *   const handleProviderUpdate = (providerId, updates) => {
 *     updateProvider(providerId, updates)
 *   }
 *   
 *   return (
 *     <div>
 *       {Object.entries(aiProviders).map(([id, provider]) => (
 *         <div key={id}>
 *           <h3>{provider.display_name}</h3>
 *           <button onClick={() => testProvider(id)}>
 *             Test Provider
 *           </button>
 *         </div>
 *       ))}
 *     </div>
 *   )
 * }
 * ```
 */
export function useSettings() {
  const context = useSettingsContext()
  
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider')
  }

  // Destructure context for easier access
  const {
    // State
    config,
    aiProviders,
    appSettings,
    activeServices,
    isLoading,
    isSaving,
    testing,
    testResults,
    error,
    success,
    showApiKeys,
    
    // Actions
    loadConfig,
    saveConfig,
    updateProviderConfig,
    updateAppSettings,
    updateActiveServices,
    testProvider,
    testAllProviders,
    toggleApiKeyVisibility,
    resetToDefaults,
    clearError,
    clearSuccess
  } = context

  /**
   * Update AI provider configuration
   * @param {string} providerId - Provider ID
   * @param {Object} updates - Configuration updates
   */
  const updateProvider = (providerId, updates) => {
    updateProviderConfig(providerId, updates)
  }

  /**
   * Update application settings
   * @param {Object} updates - Settings updates
   */
  const updateAppConfig = (updates) => {
    updateAppSettings(updates)
  }

  /**
   * Update active service providers
   * @param {Object} updates - Service updates
   */
  const updateServices = (updates) => {
    updateActiveServices(updates)
  }

  /**
   * Check if a provider is enabled
   * @param {string} providerId - Provider ID
   * @returns {boolean} Whether the provider is enabled
   */
  const isProviderEnabled = (providerId) => {
    return aiProviders[providerId]?.enabled === true
  }

  /**
   * Check if a provider is being tested
   * @param {string} providerId - Provider ID
   * @returns {boolean} Whether the provider is being tested
   */
  const isProviderTesting = (providerId) => {
    return testing[providerId] === true
  }

  /**
   * Get provider test result
   * @param {string} providerId - Provider ID
   * @returns {Object|null} Test result or null
   */
  const getProviderTestResult = (providerId) => {
    return testResults[providerId] || null
  }

  /**
   * Get provider status (enabled, testing, test result)
   * @param {string} providerId - Provider ID
   * @returns {Object} Provider status information
   */
  const getProviderStatus = (providerId) => {
    const provider = aiProviders[providerId]
    const testResult = getProviderTestResult(providerId)
    
    return {
      exists: !!provider,
      enabled: isProviderEnabled(providerId),
      testing: isProviderTesting(providerId),
      testResult,
      hasTestResult: !!testResult,
      testPassed: testResult?.success === true,
      testFailed: testResult?.success === false,
      displayName: provider?.display_name || providerId,
      type: provider?.type,
      capabilities: {
        htr: provider?.is_htr_capable === true,
        formatting: provider?.is_formatting_capable === true,
        vlm: provider?.is_vlm_capable === true
      }
    }
  }

  /**
   * Get enabled providers
   * @returns {Array} Array of enabled provider IDs
   */
  const getEnabledProviders = () => {
    return Object.keys(aiProviders).filter(id => isProviderEnabled(id))
  }

  /**
   * Get providers by capability
   * @param {string} capability - Capability type ('htr' | 'formatting' | 'vlm')
   * @returns {Array} Array of provider IDs with the capability
   */
  const getProvidersByCapability = (capability) => {
    const capabilityMap = {
      htr: 'is_htr_capable',
      formatting: 'is_formatting_capable',
      vlm: 'is_vlm_capable'
    }
    
    const capabilityKey = capabilityMap[capability]
    if (!capabilityKey) return []
    
    return Object.entries(aiProviders)
      .filter(([id, provider]) => provider[capabilityKey] === true && isProviderEnabled(id))
      .map(([id]) => id)
  }

  /**
   * Get HTR-capable providers
   * @returns {Array} Array of HTR provider IDs
   */
  const getHTRProviders = () => {
    return getProvidersByCapability('htr')
  }

  /**
   * Get formatting-capable providers
   * @returns {Array} Array of formatting provider IDs
   */
  const getFormattingProviders = () => {
    return getProvidersByCapability('formatting')
  }

  /**
   * Get VLM-capable providers
   * @returns {Array} Array of VLM provider IDs
   */
  const getVLMProviders = () => {
    return getProvidersByCapability('vlm')
  }

  /**
   * Check if API key is visible for a provider
   * @param {string} providerId - Provider ID
   * @returns {boolean} Whether API key is visible
   */
  const isApiKeyVisible = (providerId) => {
    return showApiKeys[providerId] === true
  }

  /**
   * Toggle API key visibility for a provider
   * @param {string} providerId - Provider ID
   */
  const toggleApiKey = (providerId) => {
    toggleApiKeyVisibility(providerId)
  }

  /**
   * Validate provider configuration
   * @param {string} providerId - Provider ID
   * @returns {Object} Validation result
   */
  const validateProvider = (providerId) => {
    const provider = aiProviders[providerId]
    if (!provider) {
      return {
        valid: false,
        errors: ['Provider not found']
      }
    }

    const errors = []
    
    // Check required fields
    if (!provider.display_name?.trim()) {
      errors.push('Display name is required')
    }
    
    if (!provider.type?.trim()) {
      errors.push('Provider type is required')
    }
    
    if (!provider.model?.trim()) {
      errors.push('Model is required')
    }
    
    // Check type-specific requirements
    if (provider.type === 'anthropic') {
      if (!provider.api_key?.trim() || provider.api_key === '${ANTHROPIC_API_KEY}') {
        errors.push('Valid API key is required for Anthropic providers')
      }
    }
    
    if (provider.type === 'ollama') {
      if (!provider.api_base_url?.trim()) {
        errors.push('API base URL is required for Ollama providers')
      }
    }
    
    // Check capabilities
    const hasCapability = provider.is_htr_capable || provider.is_formatting_capable || provider.is_vlm_capable
    if (!hasCapability) {
      errors.push('Provider must have at least one capability enabled')
    }

    return {
      valid: errors.length === 0,
      errors
    }
  }

  /**
   * Validate all providers
   * @returns {Object} Validation results for all providers
   */
  const validateAllProviders = () => {
    const results = {}
    Object.keys(aiProviders).forEach(providerId => {
      results[providerId] = validateProvider(providerId)
    })
    return results
  }

  /**
   * Check if configuration is valid
   * @returns {boolean} Whether configuration is valid
   */
  const isConfigValid = () => {
    const validationResults = validateAllProviders()
    return Object.values(validationResults).every(result => result.valid)
  }

  /**
   * Get configuration summary
   * @returns {Object} Configuration summary
   */
  const getConfigSummary = () => {
    const totalProviders = Object.keys(aiProviders).length
    const enabledProviders = getEnabledProviders().length
    const htrProviders = getHTRProviders().length
    const formattingProviders = getFormattingProviders().length
    const vlmProviders = getVLMProviders().length
    
    return {
      totalProviders,
      enabledProviders,
      htrProviders,
      formattingProviders,
      vlmProviders,
      activeHTRProvider: activeServices.htr_provider_id,
      activeFormattingProvider: activeServices.formatting_provider_id,
      isValid: isConfigValid()
    }
  }

  /**
   * Export configuration
   * @param {Object} options - Export options
   * @returns {string|null} Exported configuration or null if failed
   */
  const exportConfig = (options = {}) => {
    const { 
      includeApiKeys = false,
      format = 'json' 
    } = options
    
    try {
      let configToExport = { ...config }
      
      if (!includeApiKeys) {
        // Remove API keys from export
        configToExport = {
          ...configToExport,
          ai_provider_configs: Object.fromEntries(
            Object.entries(configToExport.ai_provider_configs || {}).map(([id, provider]) => [
              id,
              {
                ...provider,
                api_key: provider.api_key ? '[REDACTED]' : undefined
              }
            ])
          )
        }
      }
      
      if (format === 'json') {
        return JSON.stringify(configToExport, null, 2)
      }
      
      return JSON.stringify(configToExport, null, 2)
    } catch (error) {
      console.error('Export failed:', error)
      return null
    }
  }

  /**
   * Import configuration
   * @param {string} configData - Configuration JSON string
   * @returns {boolean} Success status
   */
  const importConfig = (configData) => {
    try {
      const importedConfig = JSON.parse(configData)
      
      // Basic validation
      if (!importedConfig || typeof importedConfig !== 'object') {
        throw new Error('Invalid configuration format')
      }
      
      // You might want to add more validation here
      
      // For now, we'll just update the context state
      // In a real implementation, you might want to call a specific import action
      console.log('Configuration import would update:', importedConfig)
      
      return true
    } catch (error) {
      console.error('Import failed:', error)
      return false
    }
  }

  /**
   * Reset specific provider to defaults
   * @param {string} providerId - Provider ID to reset
   */
  const resetProvider = (providerId) => {
    if (window.confirm(`Are you sure you want to reset ${providerId} to defaults?`)) {
      // This would need to be implemented based on your default configurations
      console.log(`Reset provider: ${providerId}`)
    }
  }

  /**
   * Check if there are unsaved changes
   * @returns {boolean} Whether there are unsaved changes
   */
  const hasUnsavedChanges = () => {
    // This would need to track changes against the last saved state
    // For now, we'll return false
    return false
  }

  /**
   * Save configuration with validation
   * @returns {Promise<boolean>} Success status
   */
  const saveConfigWithValidation = async () => {
    if (!isConfigValid()) {
      const validationResults = validateAllProviders()
      const errors = Object.entries(validationResults)
        .filter(([, result]) => !result.valid)
        .map(([id, result]) => `${id}: ${result.errors.join(', ')}`)
      
      const proceed = window.confirm(
        `Configuration has validation errors:\n${errors.join('\n')}\n\nSave anyway?`
      )
      
      if (!proceed) return false
    }
    
    try {
      await saveConfig()
      return true
    } catch (error) {
      console.error('Save failed:', error)
      return false
    }
  }

  return {
    // State
    config,
    aiProviders,
    appSettings,
    activeServices,
    isLoading,
    isSaving,
    testing,
    testResults,
    error,
    success,
    showApiKeys,
    
    // Basic actions
    loadConfig,
    saveConfig,
    updateProviderConfig,
    updateAppSettings,
    updateActiveServices,
    testProvider,
    testAllProviders,
    toggleApiKeyVisibility,
    resetToDefaults,
    clearError,
    clearSuccess,
    
    // Utility functions
    updateProvider,
    updateAppConfig,
    updateServices,
    isProviderEnabled,
    isProviderTesting,
    getProviderTestResult,
    getProviderStatus,
    getEnabledProviders,
    getProvidersByCapability,
    getHTRProviders,
    getFormattingProviders,
    getVLMProviders,
    isApiKeyVisible,
    toggleApiKey,
    validateProvider,
    validateAllProviders,
    isConfigValid,
    getConfigSummary,
    exportConfig,
    importConfig,
    resetProvider,
    hasUnsavedChanges,
    saveConfigWithValidation
  }
}

export default useSettings