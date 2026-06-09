import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { FileText } from 'lucide-react'
import { uploadPDF } from '../services/api'

const FileUpload = ({ onSuccess }) => {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return
    const file = acceptedFiles[0]
    setSelectedFile(file)
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

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { 'application/pdf': ['.pdf'] }, maxFiles: 1 })

  return (
    <div
  className="centered anim-fade-up"
  style={{
    width: '100%',
    maxWidth: '850px',
    margin: '0 auto'
  }}
>
      <div
  style={{
    textAlign: 'center',
    marginBottom: '28px',
    width: '100%'
  }}
>
  <h2
    style={{
      fontWeight: 800,
      fontSize: 'clamp(2rem,5vw,3rem)',
      marginBottom: '12px',
      lineHeight: 1.2
    }}
  >
    Upload your PDF
  </h2>

  <p
    style={{
      color: 'var(--text-secondary)',
      fontSize: '1.1rem'
    }}
  >
    Drop any document — lectures, textbooks, research papers
  </p>
</div>

      <div {...getRootProps()} className="card upload-drop" style={{marginTop:18,width:'100%'}}>
        <input {...getInputProps()} disabled={uploading} />
        <div className="upload-icon">
          <FileText style={{width:36,height:36,color:'var(--accent-purple)'}} />
        </div>

        {uploading ? (
          <div>
            <div style={{fontWeight:700}}>Processing PDF…</div>
            {selectedFile && <div style={{color:'var(--text-secondary)',marginTop:6}}>{selectedFile.name}</div>}
          </div>
        ) : (
          <div>
            <div style={{fontWeight:700}}>Drop your PDF here</div>
            <div style={{color:'var(--text-secondary)',marginTop:8}}>or <span style={{color:'var(--accent-purple)'}}>click to browse</span></div>
            <div style={{marginTop:12,display:'inline-block',padding:'6px 10px',borderRadius:999,border:'1px solid var(--muted)',color:'var(--text-secondary)'}}>PDF · up to 50 MB</div>
          </div>
        )}
      </div>

      {error && <div className="card" style={{marginTop:12,background:'rgba(247,83,83,0.03)',borderColor:'rgba(247,83,83,0.12)'}}>{error}</div>}
    </div>
  )
}

export default FileUpload