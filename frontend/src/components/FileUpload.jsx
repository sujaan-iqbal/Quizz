import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText } from 'lucide-react'
import { uploadPDF } from '../services/api'

const FileUpload = ({ onSuccess }) => {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return
    
    const file = acceptedFiles[0]
    setUploading(true)
    setError(null)
    
    try {
      const response = await uploadPDF(file)
      onSuccess(response)
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }, [onSuccess])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1
  })

  return (
    <div className="max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-purple-500 bg-purple-500/10' : 'border-gray-600 hover:border-gray-500'}
          ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} disabled={uploading} />
        {uploading ? (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
            <p className="text-gray-300">Uploading and processing PDF...</p>
          </>
        ) : isDragActive ? (
          <>
            <Upload className="mx-auto h-12 w-12 text-purple-500 mb-4" />
            <p className="text-gray-300">Drop the PDF here...</p>
          </>
        ) : (
          <>
            <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-300">Drag & drop a PDF file here</p>
            <p className="text-gray-500 text-sm mt-2">or click to select</p>
            <p className="text-gray-600 text-xs mt-4">PDF up to 50MB</p>
          </>
        )}
      </div>
      {error && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500 rounded text-red-500 text-sm">
          {error}
        </div>
      )}
    </div>
  )
}

export default FileUpload
