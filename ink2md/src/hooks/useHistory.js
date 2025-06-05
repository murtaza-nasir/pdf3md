/**
 * @fileoverview useHistory hook - Custom hook for HistoryContext
 * 
 * Provides convenient access to conversion history state and operations.
 * This hook wraps the HistoryContext and provides additional utility functions
 * for history management, search, and filtering.
 * 
 * @author Sarah Wolff
 * @version 0.5 beta
 */

import { useHistory as useHistoryContext } from '../contexts/HistoryContext'

/**
 * Custom hook for accessing and managing conversion history
 * 
 * @returns {Object} History state and utility functions
 * @throws {Error} If used outside of HistoryProvider
 * 
 * @example
 * ```jsx
 * function HistoryPanel() {
 *   const { 
 *     filteredItems,
 *     selectedId,
 *     searchQuery,
 *     handleSearch,
 *     selectAndDisplay,
 *     getSelectedItem
 *   } = useHistory()
 *   
 *   const selectedItem = getSelectedItem()
 *   
 *   return (
 *     <div>
 *       <input 
 *         value={searchQuery} 
 *         onChange={(e) => handleSearch(e.target.value)} 
 *         placeholder="Search history..."
 *       />
 *       {filteredItems.map(item => (
 *         <div key={item.id} onClick={() => selectAndDisplay(item.id)}>
 *           {item.filename}
 *         </div>
 *       ))}
 *     </div>
 *   )
 * }
 * ```
 */
export function useHistory() {
  const context = useHistoryContext()
  
  if (!context) {
    throw new Error('useHistory must be used within a HistoryProvider')
  }

  // Destructure context for easier access
  const {
    // State
    items,
    filteredItems,
    selectedId,
    searchQuery,
    sortBy,
    sortOrder,
    filterBy,
    isLoading,
    
    // Actions
    addItem,
    removeItem,
    clearHistory,
    selectItem,
    toggleFavorite,
    addTag,
    removeTag,
    setSearch,
    setSorting,
    setFilter,
    exportHistory,
    importHistory,
    getSelectedItem
  } = context

  /**
   * Handle search with debouncing
   * @param {string} query - Search query
   */
  const handleSearch = (query) => {
    setSearch(query)
  }

  /**
   * Select item and return its content for display
   * @param {number} itemId - Item ID to select
   * @returns {Object|null} Selected item or null
   */
  const selectAndDisplay = (itemId) => {
    selectItem(itemId)
    return getSelectedItem()
  }

  /**
   * Get items by date range
   * @param {Date} startDate - Start date
   * @param {Date} endDate - End date
   * @returns {Array} Items within date range
   */
  const getItemsByDateRange = (startDate, endDate) => {
    return items.filter(item => {
      const itemDate = new Date(item.timestamp)
      return itemDate >= startDate && itemDate <= endDate
    })
  }

  /**
   * Get items from today
   * @returns {Array} Today's items
   */
  const getTodaysItems = () => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)
    
    return getItemsByDateRange(today, tomorrow)
  }

  /**
   * Get items from this week
   * @returns {Array} This week's items
   */
  const getThisWeeksItems = () => {
    const now = new Date()
    const startOfWeek = new Date(now)
    startOfWeek.setDate(now.getDate() - now.getDay())
    startOfWeek.setHours(0, 0, 0, 0)
    
    return getItemsByDateRange(startOfWeek, now)
  }

  /**
   * Get favorite items
   * @returns {Array} Favorite items
   */
  const getFavoriteItems = () => {
    return items.filter(item => item.favorite)
  }

  /**
   * Get items by tag
   * @param {string} tag - Tag to filter by
   * @returns {Array} Items with the specified tag
   */
  const getItemsByTag = (tag) => {
    return items.filter(item => item.tags && item.tags.includes(tag))
  }

  /**
   * Get all unique tags
   * @returns {Array<string>} Array of unique tags
   */
  const getAllTags = () => {
    const tagSet = new Set()
    items.forEach(item => {
      if (item.tags) {
        item.tags.forEach(tag => tagSet.add(tag))
      }
    })
    return Array.from(tagSet).sort()
  }

  /**
   * Get statistics about the history
   * @returns {Object} History statistics
   */
  const getHistoryStats = () => {
    const total = items.length
    const favorites = getFavoriteItems().length
    const totalSize = items.reduce((sum, item) => sum + (item.fileSize || 0), 0)
    const totalPages = items.reduce((sum, item) => sum + (item.pageCount || 0), 0)
    const uniqueTags = getAllTags().length
    
    // Get conversion frequency by day
    const conversionsByDay = {}
    items.forEach(item => {
      const date = new Date(item.timestamp).toDateString()
      conversionsByDay[date] = (conversionsByDay[date] || 0) + 1
    })
    
    const avgConversionsPerDay = Object.keys(conversionsByDay).length > 0 
      ? Object.values(conversionsByDay).reduce((sum, count) => sum + count, 0) / Object.keys(conversionsByDay).length
      : 0

    return {
      total,
      favorites,
      totalSize,
      totalPages,
      uniqueTags,
      avgConversionsPerDay: Math.round(avgConversionsPerDay * 100) / 100,
      conversionsByDay
    }
  }

  /**
   * Format file size for display
   * @param {number} bytes - Size in bytes
   * @returns {string} Formatted size string
   */
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  /**
   * Format timestamp for display
   * @param {string} timestamp - ISO timestamp
   * @param {Object} options - Formatting options
   * @returns {string} Formatted timestamp
   */
  const formatTimestamp = (timestamp, options = {}) => {
    const { 
      includeTime = true, 
      includeDate = true, 
      relative = false 
    } = options
    
    const date = new Date(timestamp)
    const now = new Date()
    
    if (relative) {
      const diffMs = now - date
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)
      
      if (diffMins < 1) return 'Just now'
      if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
      if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
      if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
    }
    
    let formatted = ''
    
    if (includeDate) {
      formatted += date.toLocaleDateString()
    }
    
    if (includeTime) {
      if (formatted) formatted += ' '
      formatted += date.toLocaleTimeString()
    }
    
    return formatted
  }

  /**
   * Toggle sorting order for current sort field
   */
  const toggleSortOrder = () => {
    const newOrder = sortOrder === 'asc' ? 'desc' : 'asc'
    setSorting(sortBy, newOrder)
  }

  /**
   * Change sort field and set default order
   * @param {string} field - Sort field ('date' | 'name' | 'size')
   */
  const changeSortField = (field) => {
    const defaultOrder = field === 'date' ? 'desc' : 'asc'
    setSorting(field, defaultOrder)
  }

  /**
   * Quick filter shortcuts
   */
  const filterShortcuts = {
    showAll: () => setFilter('all'),
    showFavorites: () => setFilter('favorites'),
    showRecent: () => setFilter('recent')
  }

  /**
   * Bulk operations
   */
  const bulkOperations = {
    /**
     * Add tag to multiple items
     * @param {Array<number>} itemIds - Item IDs
     * @param {string} tag - Tag to add
     */
    addTagToItems: (itemIds, tag) => {
      itemIds.forEach(id => addTag(id, tag))
    },

    /**
     * Remove tag from multiple items
     * @param {Array<number>} itemIds - Item IDs
     * @param {string} tag - Tag to remove
     */
    removeTagFromItems: (itemIds, tag) => {
      itemIds.forEach(id => removeTag(id, tag))
    },

    /**
     * Toggle favorite for multiple items
     * @param {Array<number>} itemIds - Item IDs
     */
    toggleFavoriteForItems: (itemIds) => {
      itemIds.forEach(id => toggleFavorite(id))
    },

    /**
     * Remove multiple items
     * @param {Array<number>} itemIds - Item IDs
     */
    removeItems: (itemIds) => {
      if (window.confirm(`Are you sure you want to delete ${itemIds.length} item(s)?`)) {
        itemIds.forEach(id => removeItem(id))
      }
    }
  }

  /**
   * Export history with options
   * @param {Object} options - Export options
   * @returns {string|null} Exported data or null if failed
   */
  const exportHistoryWithOptions = (options = {}) => {
    const { 
      includeMarkdown = true, 
      includeMetadata = true,
      format = 'json' 
    } = options
    
    try {
      let dataToExport = items
      
      if (!includeMarkdown || !includeMetadata) {
        dataToExport = items.map(item => {
          const exported = { ...item }
          if (!includeMarkdown) delete exported.markdown
          if (!includeMetadata) {
            // Keep only essential fields
            return {
              id: exported.id,
              filename: exported.filename,
              timestamp: exported.timestamp,
              ...(includeMarkdown && { markdown: exported.markdown })
            }
          }
          return exported
        })
      }
      
      if (format === 'json') {
        return JSON.stringify(dataToExport, null, 2)
      }
      
      // Could add other formats like CSV here
      return JSON.stringify(dataToExport, null, 2)
    } catch (error) {
      console.error('Export failed:', error)
      return null
    }
  }

  /**
   * Check if history is empty
   * @returns {boolean} Whether history is empty
   */
  const isEmpty = () => {
    return items.length === 0
  }

  /**
   * Check if search is active
   * @returns {boolean} Whether search is active
   */
  const isSearchActive = () => {
    return searchQuery.trim().length > 0
  }

  /**
   * Check if filters are active
   * @returns {boolean} Whether filters are active
   */
  const isFilterActive = () => {
    return filterBy !== 'all' || isSearchActive()
  }

  return {
    // State
    items,
    filteredItems,
    selectedId,
    searchQuery,
    sortBy,
    sortOrder,
    filterBy,
    isLoading,
    
    // Basic actions
    addItem,
    removeItem,
    clearHistory,
    selectItem,
    toggleFavorite,
    addTag,
    removeTag,
    setSearch,
    setSorting,
    setFilter,
    exportHistory,
    importHistory,
    getSelectedItem,
    
    // Utility functions
    handleSearch,
    selectAndDisplay,
    getItemsByDateRange,
    getTodaysItems,
    getThisWeeksItems,
    getFavoriteItems,
    getItemsByTag,
    getAllTags,
    getHistoryStats,
    formatFileSize,
    formatTimestamp,
    toggleSortOrder,
    changeSortField,
    filterShortcuts,
    bulkOperations,
    exportHistoryWithOptions,
    isEmpty,
    isSearchActive,
    isFilterActive
  }
}

export default useHistory