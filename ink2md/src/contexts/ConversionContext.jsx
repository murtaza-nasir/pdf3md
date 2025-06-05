/**
 * @fileoverview ConversionContext - File conversion state management
 * 
 * Manages file conversion operations including:
 * - File upload queue management
 * - Processing states and progress tracking
 * - Multi-file batch processing
 * - Conversion results and error handling
 * - Backend communication for conversions
 * 
 * @author Sarah Wolff
 * @version 0.5
 */

import { createContext, useContext, useReducer, useRef, useCallback } from 'react'

/**
 * @typedef {Object} FileState
 * @property {string} name - File name
 * @property {number} size - File size in bytes
 * @property {string} type - File type
 * @property {string} status - Processing status ('queued' | 'uploading' | 'processing' | 'completed' | 'error' | 'skipped')
 * @property {number} progress - Progress percentage (0-100)
 * @property {string} stage - Current processing stage
 * @property {number} totalPages - Total pages in document
 * @property {number} currentPage - Current page being processed
 * @property {string|null} markdown - Converted markdown content
 * @property {string|null} error - Error message if failed
 * @property {File} originalFile - Original file object
 */

/**
 * @typedef {Object} ConversionState
 * @property {Array<File>} uploadQueue - Files waiting to be processed
 * @property {Array<FileState>} fileStates - Current state of all files
 * @property {File|null} currentFile - File currently being processed
 * @property {string|null} activeConversionId - Current conversion ID for polling
 * @property {boolean} isProcessing - Whether any file is currently processing
 * @property {string} markdown - Current markdown display content
 */

/**
 * @typedef {Object} ConversionActions
 * @property {Function} addFiles - Add files to processing queue
 * @property {Function} removeFile - Remove file from queue/states
 * @property {Function} retryFile - Retry failed file conversion
 * @property {Function} clearCompleted - Clear completed file states
 * @property {Function} clearAll - Clear all files and states
 * @property {Function} updateFileStatus - Update specific file status
 * @property {Function} setMarkdown - Set current markdown content
 * @property {Function} processNextFile - Process next file in queue
 */

// Initial state
const initialState = {
  uploadQueue: [],
  fileStates: [],
  currentFile: null,
  activeConversionId: null,
  isProcessing: false,
  markdown: ''
}

// Action types
const ActionTypes = {
  ADD_FILES: 'ADD_FILES',
  REMOVE_FILE: 'REMOVE_FILE',
  UPDATE_FILE_STATUS: 'UPDATE_FILE_STATUS',
  SET_CURRENT_FILE: 'SET_CURRENT_FILE',
  SET_ACTIVE_CONVERSION_ID: 'SET_ACTIVE_CONVERSION_ID',
  SET_PROCESSING: 'SET_PROCESSING',
  SET_MARKDOWN: 'SET_MARKDOWN',
  CLEAR_COMPLETED: 'CLEAR_COMPLETED',
  CLEAR_ALL: 'CLEAR_ALL',
  PROCESS_NEXT_FILE: 'PROCESS_NEXT_FILE',
  RETRY_FILE: 'RETRY_FILE'
}

/**
 * Conversion state reducer
 * @param {ConversionState} state - Current state
 * @param {Object} action - Action object with type and payload
 * @returns {ConversionState} New state
 */
function conversionReducer(state, action) {
  switch (action.type) {
    case ActionTypes.ADD_FILES: {
      const { files, replaceExisting } = action.payload
      const newFileStates = files.map(file => ({
        name: file.name,
        size: file.size,
        type: file.type.includes('pdf') || file.name.toLowerCase().endsWith('.pdf') ? 'pdf' : 'unknown',
        status: 'queued',
        progress: 0,
        stage: 'Queued',
        totalPages: 0,
        currentPage: 0,
        markdown: null,
        error: null,
        originalFile: file
      }))

      const existingStates = replaceExisting ? [] : state.fileStates
      const isPreviousBatchDone = state.fileStates.every(f => 
        f.status === 'completed' || f.status === 'error' || f.status === 'skipped'
      )

      return {
        ...state,
        uploadQueue: [...state.uploadQueue, ...files],
        fileStates: isPreviousBatchDone || replaceExisting ? newFileStates : [...existingStates, ...newFileStates]
      }
    }

    case ActionTypes.REMOVE_FILE:
      return {
        ...state,
        uploadQueue: state.uploadQueue.filter(file => file.name !== action.payload),
        fileStates: state.fileStates.filter(fileState => fileState.name !== action.payload)
      }

    case ActionTypes.UPDATE_FILE_STATUS:
      return {
        ...state,
        fileStates: state.fileStates.map(fileState =>
          fileState.name === action.payload.fileName
            ? { ...fileState, ...action.payload.updates }
            : fileState
        )
      }

    case ActionTypes.SET_CURRENT_FILE:
      return {
        ...state,
        currentFile: action.payload
      }

    case ActionTypes.SET_ACTIVE_CONVERSION_ID:
      return {
        ...state,
        activeConversionId: action.payload
      }

    case ActionTypes.SET_PROCESSING:
      return {
        ...state,
        isProcessing: action.payload
      }

    case ActionTypes.SET_MARKDOWN:
      return {
        ...state,
        markdown: action.payload
      }

    case ActionTypes.CLEAR_COMPLETED:
      return {
        ...state,
        fileStates: state.fileStates.filter(fileState => 
          fileState.status !== 'completed' && fileState.status !== 'skipped'
        )
      }

    case ActionTypes.CLEAR_ALL:
      return {
        ...initialState,
        markdown: state.markdown // Preserve current markdown display
      }

    case ActionTypes.PROCESS_NEXT_FILE:
      if (state.uploadQueue.length === 0) {
        return {
          ...state,
          isProcessing: false,
          currentFile: null
        }
      }

      const nextFile = state.uploadQueue[0]
      return {
        ...state,
        uploadQueue: state.uploadQueue.slice(1),
        currentFile: nextFile,
        isProcessing: true
      }

    case ActionTypes.RETRY_FILE: {
      const fileName = action.payload
      const fileState = state.fileStates.find(f => f.name === fileName)
      
      if (!fileState) return state

      return {
        ...state,
        uploadQueue: [fileState.originalFile, ...state.uploadQueue],
        fileStates: state.fileStates.map(f =>
          f.name === fileName
            ? { ...f, status: 'queued', stage: 'Queued', progress: 0, error: null }
            : f
        )
      }
    }

    default:
      return state
  }
}

// Create context
const ConversionContext = createContext(null)

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
 * ConversionProvider component
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components
 * @param {Function} props.onAddToHistory - Callback to add conversion to history
 * @returns {JSX.Element} Provider component
 */
export function ConversionProvider({ children, onAddToHistory }) {
  const [state, dispatch] = useReducer(conversionReducer, initialState)
  const activeConversionId = useRef(null)

  /**
   * Update file status
   * @param {string} fileName - File name
   * @param {Object} updates - Status updates
   */
  const updateFileStatus = useCallback((fileName, updates) => {
    dispatch({
      type: ActionTypes.UPDATE_FILE_STATUS,
      payload: { fileName, updates }
    })
  }, [])

  /**
   * Poll conversion progress
   * @param {string} conversionId - Conversion ID
   * @param {string} fileName - File name
   */
  const pollProgress = useCallback(async (conversionId, fileName) => {
    activeConversionId.current = conversionId
    dispatch({ type: ActionTypes.SET_ACTIVE_CONVERSION_ID, payload: conversionId })

    const pollInterval = setInterval(async () => {
      if (activeConversionId.current !== conversionId) {
        clearInterval(pollInterval)
        return
      }

      try {
        const response = await fetch(`${getBackendUrl()}/progress/${conversionId}`)
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
        
        const progressData = await response.json()

        updateFileStatus(fileName, {
          progress: progressData.progress || 0,
          stage: progressData.stage || 'Processing...',
          totalPages: progressData.total_pages || 0,
          currentPage: progressData.current_page || 0
        })

        if (progressData.status === 'completed' && progressData.result) {
          clearInterval(pollInterval)
          activeConversionId.current = null
          
          // Update file status to completed
          updateFileStatus(fileName, {
            status: 'completed',
            markdown: progressData.result.markdown,
            progress: 100
          })

          // Add to history if callback provided
          if (onAddToHistory) {
            onAddToHistory(progressData.result)
          }

          // Set current markdown display
          dispatch({ type: ActionTypes.SET_MARKDOWN, payload: progressData.result.markdown })

          // Process next file
          dispatch({ type: ActionTypes.PROCESS_NEXT_FILE })
          
        } else if (progressData.status === 'error') {
          clearInterval(pollInterval)
          activeConversionId.current = null
          
          updateFileStatus(fileName, {
            status: 'error',
            error: progressData.error || 'Unknown conversion error',
            progress: 0,
            stage: 'Error'
          })

          // Process next file
          dispatch({ type: ActionTypes.PROCESS_NEXT_FILE })
        }
      } catch (error) {
        console.error('Error polling progress:', error)
        clearInterval(pollInterval)
        activeConversionId.current = null
        
        updateFileStatus(fileName, {
          status: 'error',
          error: `Polling failed: ${error.message}`,
          progress: 0,
          stage: 'Error'
        })

        // Process next file
        dispatch({ type: ActionTypes.PROCESS_NEXT_FILE })
      }
    }, 500)

    return pollInterval
  }, [updateFileStatus, onAddToHistory])

  /**
   * Process a single file
   * @param {File} file - File to process
   */
  const processFile = useCallback(async (file) => {
    if (!file) return

    const isPdf = file.type.includes('pdf') || file.name.toLowerCase().endsWith('.pdf')

    if (!isPdf) {
      updateFileStatus(file.name, {
        status: 'skipped',
        error: 'Unsupported file type'
      })
      dispatch({ type: ActionTypes.PROCESS_NEXT_FILE })
      return
    }

    dispatch({ type: ActionTypes.SET_CURRENT_FILE, payload: file })
    dispatch({ type: ActionTypes.SET_PROCESSING, payload: true })
    
    updateFileStatus(file.name, {
      status: 'uploading',
      progress: 0,
      stage: 'Uploading file...'
    })

    const formData = new FormData()
    formData.append('pdf', file)

    try {
      const response = await fetch(`${getBackendUrl()}/convert`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
      
      const data = await response.json()

      if (data.success && data.conversion_id) {
        updateFileStatus(file.name, {
          status: 'processing',
          stage: 'Waiting for conversion...'
        })
        pollProgress(data.conversion_id, file.name)
      } else {
        throw new Error(data.error || 'PDF conversion failed to start')
      }
    } catch (err) {
      console.error(`Error during PDF conversion for ${file.name}:`, err)
      updateFileStatus(file.name, {
        status: 'error',
        error: err.message || 'Failed to start PDF conversion'
      })
      dispatch({ type: ActionTypes.PROCESS_NEXT_FILE })
    }
  }, [updateFileStatus, pollProgress])

  // Action creators
  const actions = {
    /**
     * Add files to processing queue
     * @param {FileList|Array<File>} files - Files to add
     * @param {boolean} replaceExisting - Whether to replace existing files
     */
    addFiles: useCallback((files, replaceExisting = false) => {
      const fileArray = Array.from(files).filter(file => {
        const isPdf = file.type.includes('pdf') || file.name.toLowerCase().endsWith('.pdf')
        return isPdf
      })

      if (fileArray.length === 0) {
        console.warn('No valid PDF files to add')
        return
      }

      dispatch({
        type: ActionTypes.ADD_FILES,
        payload: { files: fileArray, replaceExisting }
      })

      // Clear current markdown when adding new files
      dispatch({ type: ActionTypes.SET_MARKDOWN, payload: '' })

      // Start processing if not already processing
      if (!state.isProcessing && fileArray.length > 0) {
        setTimeout(() => processFile(fileArray[0]), 100)
      }
    }, [state.isProcessing, processFile]),

    /**
     * Remove file from queue/states
     * @param {string} fileName - File name to remove
     */
    removeFile: useCallback((fileName) => {
      dispatch({ type: ActionTypes.REMOVE_FILE, payload: fileName })
    }, []),

    /**
     * Retry failed file conversion
     * @param {string} fileName - File name to retry
     */
    retryFile: useCallback((fileName) => {
      dispatch({ type: ActionTypes.RETRY_FILE, payload: fileName })
    }, []),

    /**
     * Clear completed file states
     */
    clearCompleted: useCallback(() => {
      dispatch({ type: ActionTypes.CLEAR_COMPLETED })
    }, []),

    /**
     * Clear all files and states
     */
    clearAll: useCallback(() => {
      dispatch({ type: ActionTypes.CLEAR_ALL })
    }, []),

    /**
     * Set current markdown content
     * @param {string} markdown - Markdown content
     */
    setMarkdown: useCallback((markdown) => {
      dispatch({ type: ActionTypes.SET_MARKDOWN, payload: markdown })
    }, []),

    /**
     * Process next file in queue
     */
    processNextFile: useCallback(() => {
      if (state.uploadQueue.length > 0 && !state.isProcessing) {
        const nextFile = state.uploadQueue[0]
        processFile(nextFile)
      }
    }, [state.uploadQueue, state.isProcessing, processFile])
  }

  const contextValue = {
    ...state,
    ...actions
  }

  return (
    <ConversionContext.Provider value={contextValue}>
      {children}
    </ConversionContext.Provider>
  )
}

/**
 * Custom hook to use conversion context
 * @returns {ConversionState & ConversionActions} Conversion state and actions
 * @throws {Error} If used outside of ConversionProvider
 */
export function useConversion() {
  const context = useContext(ConversionContext)
  if (!context) {
    throw new Error('useConversion must be used within a ConversionProvider')
  }
  return context
}

export default ConversionContext