/**
 * @fileoverview HistoryContext - Conversion history management
 * 
 * Manages conversion history including:
 * - History storage and persistence
 * - Search and filtering capabilities
 * - History item selection and display
 * - Local storage synchronization
 * - History cleanup and management
 * 
 * @author Sarah Wolff
 * @version 0.5
 */

import { createContext, useContext, useReducer, useEffect, useRef, useCallback } from 'react'

/**
 * @typedef {Object} HistoryItem
 * @property {number} id - Unique identifier
 * @property {string} filename - Original filename
 * @property {string} markdown - Converted markdown content
 * @property {number} fileSize - File size in bytes
 * @property {number} pageCount - Number of pages processed
 * @property {string} timestamp - ISO timestamp of conversion
 * @property {Array<string>} tags - User-defined tags
 * @property {boolean} favorite - Whether item is favorited
 */

/**
 * @typedef {Object} HistoryState
 * @property {Array<HistoryItem>} items - All history items
 * @property {Array<HistoryItem>} filteredItems - Filtered history items
 * @property {number|null} selectedId - Currently selected item ID
 * @property {string} searchQuery - Current search query
 * @property {string} sortBy - Sort criteria ('date' | 'name' | 'size')
 * @property {string} sortOrder - Sort order ('asc' | 'desc')
 * @property {string} filterBy - Filter criteria ('all' | 'favorites' | 'recent')
 * @property {boolean} isLoading - Loading state for history operations
 */

/**
 * @typedef {Object} HistoryActions
 * @property {Function} addItem - Add new history item
 * @property {Function} removeItem - Remove history item
 * @property {Function} clearHistory - Clear all history
 * @property {Function} selectItem - Select history item
 * @property {Function} toggleFavorite - Toggle item favorite status
 * @property {Function} addTag - Add tag to item
 * @property {Function} removeTag - Remove tag from item
 * @property {Function} setSearch - Set search query
 * @property {Function} setSorting - Set sort criteria and order
 * @property {Function} setFilter - Set filter criteria
 * @property {Function} exportHistory - Export history data
 * @property {Function} importHistory - Import history data
 */

// Initial state
const initialState = {
  items: [],
  filteredItems: [],
  selectedId: null,
  searchQuery: '',
  sortBy: 'date',
  sortOrder: 'desc',
  filterBy: 'all',
  isLoading: false
}

// Action types
const ActionTypes = {
  SET_ITEMS: 'SET_ITEMS',
  ADD_ITEM: 'ADD_ITEM',
  REMOVE_ITEM: 'REMOVE_ITEM',
  CLEAR_HISTORY: 'CLEAR_HISTORY',
  SELECT_ITEM: 'SELECT_ITEM',
  TOGGLE_FAVORITE: 'TOGGLE_FAVORITE',
  ADD_TAG: 'ADD_TAG',
  REMOVE_TAG: 'REMOVE_TAG',
  SET_SEARCH: 'SET_SEARCH',
  SET_SORTING: 'SET_SORTING',
  SET_FILTER: 'SET_FILTER',
  SET_FILTERED_ITEMS: 'SET_FILTERED_ITEMS',
  SET_LOADING: 'SET_LOADING'
}

/**
 * History state reducer
 * @param {HistoryState} state - Current state
 * @param {Object} action - Action object with type and payload
 * @returns {HistoryState} New state
 */
function historyReducer(state, action) {
  switch (action.type) {
    case ActionTypes.SET_ITEMS:
      return {
        ...state,
        items: action.payload,
        filteredItems: action.payload
      }

    case ActionTypes.ADD_ITEM: {
      const newItem = {
        id: Date.now(),
        tags: [],
        favorite: false,
        ...action.payload
      }
      const newItems = [newItem, ...state.items].slice(0, 50) // Keep max 50 items
      return {
        ...state,
        items: newItems,
        filteredItems: newItems
      }
    }

    case ActionTypes.REMOVE_ITEM: {
      const newItems = state.items.filter(item => item.id !== action.payload)
      return {
        ...state,
        items: newItems,
        filteredItems: newItems,
        selectedId: state.selectedId === action.payload ? null : state.selectedId
      }
    }

    case ActionTypes.CLEAR_HISTORY:
      return {
        ...state,
        items: [],
        filteredItems: [],
        selectedId: null
      }

    case ActionTypes.SELECT_ITEM:
      return {
        ...state,
        selectedId: action.payload
      }

    case ActionTypes.TOGGLE_FAVORITE: {
      const newItems = state.items.map(item =>
        item.id === action.payload
          ? { ...item, favorite: !item.favorite }
          : item
      )
      return {
        ...state,
        items: newItems,
        filteredItems: newItems
      }
    }

    case ActionTypes.ADD_TAG: {
      const { itemId, tag } = action.payload
      const newItems = state.items.map(item =>
        item.id === itemId
          ? { ...item, tags: [...new Set([...item.tags, tag])] }
          : item
      )
      return {
        ...state,
        items: newItems,
        filteredItems: newItems
      }
    }

    case ActionTypes.REMOVE_TAG: {
      const { itemId, tag } = action.payload
      const newItems = state.items.map(item =>
        item.id === itemId
          ? { ...item, tags: item.tags.filter(t => t !== tag) }
          : item
      )
      return {
        ...state,
        items: newItems,
        filteredItems: newItems
      }
    }

    case ActionTypes.SET_SEARCH:
      return {
        ...state,
        searchQuery: action.payload
      }

    case ActionTypes.SET_SORTING:
      return {
        ...state,
        sortBy: action.payload.sortBy,
        sortOrder: action.payload.sortOrder
      }

    case ActionTypes.SET_FILTER:
      return {
        ...state,
        filterBy: action.payload
      }

    case ActionTypes.SET_FILTERED_ITEMS:
      return {
        ...state,
        filteredItems: action.payload
      }

    case ActionTypes.SET_LOADING:
      return {
        ...state,
        isLoading: action.payload
      }

    default:
      return state
  }
}

/**
 * Filter and sort history items
 * @param {Array<HistoryItem>} items - Items to filter
 * @param {string} searchQuery - Search query
 * @param {string} filterBy - Filter criteria
 * @param {string} sortBy - Sort criteria
 * @param {string} sortOrder - Sort order
 * @returns {Array<HistoryItem>} Filtered and sorted items
 */
function filterAndSortItems(items, searchQuery, filterBy, sortBy, sortOrder) {
  let filtered = [...items]

  // Apply search filter
  if (searchQuery.trim()) {
    const query = searchQuery.toLowerCase()
    filtered = filtered.filter(item =>
      item.filename.toLowerCase().includes(query) ||
      item.markdown.toLowerCase().includes(query) ||
      item.tags.some(tag => tag.toLowerCase().includes(query))
    )
  }

  // Apply category filter
  switch (filterBy) {
    case 'favorites':
      filtered = filtered.filter(item => item.favorite)
      break
    case 'recent':
      const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000)
      filtered = filtered.filter(item => new Date(item.timestamp) > oneDayAgo)
      break
    case 'all':
    default:
      // No additional filtering
      break
  }

  // Apply sorting
  filtered.sort((a, b) => {
    let comparison = 0
    
    switch (sortBy) {
      case 'name':
        comparison = a.filename.localeCompare(b.filename)
        break
      case 'size':
        comparison = a.fileSize - b.fileSize
        break
      case 'date':
      default:
        comparison = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
        break
    }

    return sortOrder === 'asc' ? comparison : -comparison
  })

  return filtered
}

// Create context
const HistoryContext = createContext(null)

// Local storage key
const HISTORY_STORAGE_KEY = 'ink2md-history'

/**
 * HistoryProvider component
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components
 * @returns {JSX.Element} Provider component
 */
export function HistoryProvider({ children }) {
  const [state, dispatch] = useReducer(historyReducer, initialState)
  const isInitialMount = useRef(true)

  // Load history from localStorage on mount
  useEffect(() => {
    const loadHistory = () => {
      try {
        const savedHistory = localStorage.getItem(HISTORY_STORAGE_KEY)
        if (savedHistory) {
          const parsedHistory = JSON.parse(savedHistory)
          if (Array.isArray(parsedHistory)) {
            dispatch({ type: ActionTypes.SET_ITEMS, payload: parsedHistory })
          }
        }
      } catch (error) {
        console.error('Error loading history from localStorage:', error)
      }
    }

    loadHistory()
  }, [])

  // Save history to localStorage when items change
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false
      return
    }

    try {
      localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(state.items))
    } catch (error) {
      console.error('Error saving history to localStorage:', error)
    }
  }, [state.items])

  // Update filtered items when search, filter, or sort changes
  useEffect(() => {
    const filtered = filterAndSortItems(
      state.items,
      state.searchQuery,
      state.filterBy,
      state.sortBy,
      state.sortOrder
    )
    dispatch({ type: ActionTypes.SET_FILTERED_ITEMS, payload: filtered })
  }, [state.items, state.searchQuery, state.filterBy, state.sortBy, state.sortOrder])

  // Action creators
  const actions = {
    /**
     * Add new history item
     * @param {Object} conversionData - Conversion result data
     */
    addItem: useCallback((conversionData) => {
      dispatch({ type: ActionTypes.ADD_ITEM, payload: conversionData })
    }, []),

    /**
     * Remove history item
     * @param {number} itemId - Item ID to remove
     */
    removeItem: useCallback((itemId) => {
      dispatch({ type: ActionTypes.REMOVE_ITEM, payload: itemId })
    }, []),

    /**
     * Clear all history
     */
    clearHistory: useCallback(() => {
      if (window.confirm('Are you sure you want to clear all conversion history? This action cannot be undone.')) {
        dispatch({ type: ActionTypes.CLEAR_HISTORY })
        localStorage.removeItem(HISTORY_STORAGE_KEY)
      }
    }, []),

    /**
     * Select history item
     * @param {number} itemId - Item ID to select
     */
    selectItem: useCallback((itemId) => {
      dispatch({ type: ActionTypes.SELECT_ITEM, payload: itemId })
    }, []),

    /**
     * Toggle item favorite status
     * @param {number} itemId - Item ID
     */
    toggleFavorite: useCallback((itemId) => {
      dispatch({ type: ActionTypes.TOGGLE_FAVORITE, payload: itemId })
    }, []),

    /**
     * Add tag to item
     * @param {number} itemId - Item ID
     * @param {string} tag - Tag to add
     */
    addTag: useCallback((itemId, tag) => {
      if (tag.trim()) {
        dispatch({ type: ActionTypes.ADD_TAG, payload: { itemId, tag: tag.trim() } })
      }
    }, []),

    /**
     * Remove tag from item
     * @param {number} itemId - Item ID
     * @param {string} tag - Tag to remove
     */
    removeTag: useCallback((itemId, tag) => {
      dispatch({ type: ActionTypes.REMOVE_TAG, payload: { itemId, tag } })
    }, []),

    /**
     * Set search query
     * @param {string} query - Search query
     */
    setSearch: useCallback((query) => {
      dispatch({ type: ActionTypes.SET_SEARCH, payload: query })
    }, []),

    /**
     * Set sorting criteria
     * @param {string} sortBy - Sort criteria
     * @param {string} sortOrder - Sort order
     */
    setSorting: useCallback((sortBy, sortOrder) => {
      dispatch({ type: ActionTypes.SET_SORTING, payload: { sortBy, sortOrder } })
    }, []),

    /**
     * Set filter criteria
     * @param {string} filterBy - Filter criteria
     */
    setFilter: useCallback((filterBy) => {
      dispatch({ type: ActionTypes.SET_FILTER, payload: filterBy })
    }, []),

    /**
     * Export history data
     * @returns {string} JSON string of history data
     */
    exportHistory: useCallback(() => {
      try {
        return JSON.stringify(state.items, null, 2)
      } catch (error) {
        console.error('Error exporting history:', error)
        return null
      }
    }, [state.items]),

    /**
     * Import history data
     * @param {string} jsonData - JSON string of history data
     * @returns {boolean} Success status
     */
    importHistory: useCallback((jsonData) => {
      try {
        const importedItems = JSON.parse(jsonData)
        if (Array.isArray(importedItems)) {
          dispatch({ type: ActionTypes.SET_ITEMS, payload: importedItems })
          return true
        }
        return false
      } catch (error) {
        console.error('Error importing history:', error)
        return false
      }
    }, []),

    /**
     * Get selected history item
     * @returns {HistoryItem|null} Selected item or null
     */
    getSelectedItem: useCallback(() => {
      return state.items.find(item => item.id === state.selectedId) || null
    }, [state.items, state.selectedId])
  }

  const contextValue = {
    ...state,
    ...actions
  }

  return (
    <HistoryContext.Provider value={contextValue}>
      {children}
    </HistoryContext.Provider>
  )
}

/**
 * Custom hook to use history context
 * @returns {HistoryState & HistoryActions} History state and actions
 * @throws {Error} If used outside of HistoryProvider
 */
export function useHistory() {
  const context = useContext(HistoryContext)
  if (!context) {
    throw new Error('useHistory must be used within a HistoryProvider')
  }
  return context
}

export default HistoryContext