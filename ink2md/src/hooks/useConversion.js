/**
 * @fileoverview useConversion hook - Custom hook for ConversionContext
 * 
 * Provides convenient access to file conversion state and operations.
 * This hook wraps the ConversionContext and provides additional utility functions
 * for file processing and queue management.
 * 
 * @author Sarah Wolff
 * @version 0.5 beta
 */

import { useConversion as useConversionContext } from '../contexts/ConversionContext'

/**
 * Custom hook for accessing and managing file conversion operations
 * 
 * @returns {Object} Conversion state and utility functions
 * @throws {Error} If used outside of ConversionProvider
 * 
 * @example
 * ```jsx
 * function FileUploader() {
 *   const { 
 *     uploadQueue,
 *     fileStates,
 *     isProcessing,
 *     handleFileUpload,
 *     getQueueStatus,
 *     hasErrors
 *   } = useConversion()
 *   
 *   const onFileSelect = (files) => {
 *     handleFileUpload(files)
 *   }
 *   
 *   return (
 *     <div>
 *       <input type="file" multiple onChange={onFileSelect} />
 *       {isProcessing && <div>Processing files...</div>}
 *       <div>Queue: {getQueueStatus()}</div>
 *     </div>
 *   )
 * }
 * ```
 */
export function useConversion() {
  const context = useConversionContext()
  
  if (!context) {
    throw new Error('useConversion must be used within a ConversionProvider')
  }

  // Destructure context for easier access
  const {
    // State
    uploadQueue,
    fileStates,
    currentFile,
    activeConversionId,
    isProcessing,
    markdown,
    
    // Actions
    addFiles,
    removeFile,
    retryFile,
    clearCompleted,
    clearAll,
    setMarkdown,
    processNextFile
  } = context

  /**
   * Handle file upload with validation
   * @param {FileList|Array<File>} files - Files to upload
   * @param {Object} options - Upload options
   * @param {boolean} options.replaceExisting - Replace existing files
   * @param {boolean} options.validatePDF - Validate PDF files (default: true)
   * @returns {Object} Upload result with success status and message
   */
  const handleFileUpload = (files, options = {}) => {
    const { replaceExisting = false, validatePDF = true } = options
    
    if (!files || files.length === 0) {
      return {
        success: false,
        message: 'No files selected'
      }
    }

    const fileArray = Array.from(files)
    
    if (validatePDF) {
      const invalidFiles = fileArray.filter(file => {
        const isPdf = file.type.includes('pdf') || file.name.toLowerCase().endsWith('.pdf')
        return !isPdf
      })
      
      if (invalidFiles.length > 0) {
        return {
          success: false,
          message: `Invalid files detected: ${invalidFiles.map(f => f.name).join(', ')}. Only PDF files are supported.`
        }
      }
    }

    addFiles(fileArray, replaceExisting)
    
    return {
      success: true,
      message: `${fileArray.length} file(s) added to queue`
    }
  }

  /**
   * Get queue status information
   * @returns {Object} Queue status details
   */
  const getQueueStatus = () => {
    const total = fileStates.length
    const queued = fileStates.filter(f => f.status === 'queued').length
    const processing = fileStates.filter(f => f.status === 'uploading' || f.status === 'processing').length
    const completed = fileStates.filter(f => f.status === 'completed').length
    const failed = fileStates.filter(f => f.status === 'error').length
    const skipped = fileStates.filter(f => f.status === 'skipped').length
    
    return {
      total,
      queued,
      processing,
      completed,
      failed,
      skipped,
      remaining: queued + processing,
      isComplete: total > 0 && (completed + failed + skipped) === total
    }
  }

  /**
   * Get files by status
   * @param {string} status - File status to filter by
   * @returns {Array} Files with the specified status
   */
  const getFilesByStatus = (status) => {
    return fileStates.filter(f => f.status === status)
  }

  /**
   * Get failed files
   * @returns {Array} Files that failed processing
   */
  const getFailedFiles = () => {
    return getFilesByStatus('error')
  }

  /**
   * Get completed files
   * @returns {Array} Files that completed successfully
   */
  const getCompletedFiles = () => {
    return getFilesByStatus('completed')
  }

  /**
   * Get processing files
   * @returns {Array} Files currently being processed
   */
  const getProcessingFiles = () => {
    return fileStates.filter(f => f.status === 'uploading' || f.status === 'processing')
  }

  /**
   * Check if there are any errors
   * @returns {boolean} Whether there are failed files
   */
  const hasErrors = () => {
    return getFailedFiles().length > 0
  }

  /**
   * Check if processing is complete
   * @returns {boolean} Whether all files are processed
   */
  const isComplete = () => {
    const status = getQueueStatus()
    return status.isComplete
  }

  /**
   * Check if queue is empty
   * @returns {boolean} Whether the queue is empty
   */
  const isQueueEmpty = () => {
    return uploadQueue.length === 0 && fileStates.length === 0
  }

  /**
   * Get overall progress percentage
   * @returns {number} Progress percentage (0-100)
   */
  const getOverallProgress = () => {
    if (fileStates.length === 0) return 0
    
    const totalProgress = fileStates.reduce((sum, file) => {
      return sum + (file.progress || 0)
    }, 0)
    
    return Math.round(totalProgress / fileStates.length)
  }

  /**
   * Get current processing file
   * @returns {Object|null} Currently processing file or null
   */
  const getCurrentFile = () => {
    return currentFile
  }

  /**
   * Retry all failed files
   * @returns {number} Number of files retried
   */
  const retryAllFailed = () => {
    const failedFiles = getFailedFiles()
    failedFiles.forEach(file => {
      retryFile(file.name)
    })
    return failedFiles.length
  }

  /**
   * Remove all failed files
   * @returns {number} Number of files removed
   */
  const removeAllFailed = () => {
    const failedFiles = getFailedFiles()
    failedFiles.forEach(file => {
      removeFile(file.name)
    })
    return failedFiles.length
  }

  /**
   * Get file by name
   * @param {string} fileName - File name to find
   * @returns {Object|null} File state or null if not found
   */
  const getFileByName = (fileName) => {
    return fileStates.find(f => f.name === fileName) || null
  }

  /**
   * Check if a file exists in the queue
   * @param {string} fileName - File name to check
   * @returns {boolean} Whether the file exists
   */
  const hasFile = (fileName) => {
    return getFileByName(fileName) !== null
  }

  /**
   * Get total file size in queue
   * @returns {number} Total size in bytes
   */
  const getTotalSize = () => {
    return fileStates.reduce((total, file) => total + (file.size || 0), 0)
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
   * Get estimated time remaining
   * @returns {string} Estimated time string
   */
  const getEstimatedTimeRemaining = () => {
    const processingFiles = getProcessingFiles()
    if (processingFiles.length === 0) return 'Unknown'
    
    // Simple estimation based on current progress
    const avgProgress = processingFiles.reduce((sum, file) => sum + file.progress, 0) / processingFiles.length
    if (avgProgress === 0) return 'Calculating...'
    
    const remainingProgress = 100 - avgProgress
    const estimatedMinutes = Math.ceil(remainingProgress / 10) // Rough estimate
    
    if (estimatedMinutes < 1) return 'Less than 1 minute'
    if (estimatedMinutes === 1) return '1 minute'
    return `${estimatedMinutes} minutes`
  }

  /**
   * Clear completed files and optionally skipped files
   * @param {boolean} includeSkipped - Whether to clear skipped files too
   */
  const clearCompletedFiles = (includeSkipped = false) => {
    if (includeSkipped) {
      // Remove both completed and skipped files
      const toRemove = fileStates.filter(f => f.status === 'completed' || f.status === 'skipped')
      toRemove.forEach(file => removeFile(file.name))
    } else {
      clearCompleted()
    }
  }

  return {
    // State
    uploadQueue,
    fileStates,
    currentFile,
    activeConversionId,
    isProcessing,
    markdown,
    
    // Basic actions
    addFiles,
    removeFile,
    retryFile,
    clearCompleted,
    clearAll,
    setMarkdown,
    processNextFile,
    
    // Utility functions
    handleFileUpload,
    getQueueStatus,
    getFilesByStatus,
    getFailedFiles,
    getCompletedFiles,
    getProcessingFiles,
    hasErrors,
    isComplete,
    isQueueEmpty,
    getOverallProgress,
    getCurrentFile,
    retryAllFailed,
    removeAllFailed,
    getFileByName,
    hasFile,
    getTotalSize,
    formatFileSize,
    getEstimatedTimeRemaining,
    clearCompletedFiles
  }
}

export default useConversion