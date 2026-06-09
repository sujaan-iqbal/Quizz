import React, { useState } from 'react'
import { signUp } from '../services/supabase'

const Signup = ({ onSuccess, onToggle }) => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const result = await signUp(email, password, fullName)
      if (result.error) throw result.error
      onSuccess()
    } catch (err) {
      setError(err.message || 'Failed to create account')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <div style={{marginBottom:10}}>
          <label style={{display:'block',marginBottom:6,fontSize:12,fontWeight:600,color:'var(--text-secondary)'}}>Full Name</label>
          <input type="text" placeholder="Jane Smith" value={fullName} onChange={(e)=>setFullName(e.target.value)} className="input" required />
        </div>

        <div style={{marginBottom:10}}>
          <label style={{display:'block',marginBottom:6,fontSize:12,fontWeight:600,color:'var(--text-secondary)'}}>Email</label>
          <input type="email" placeholder="you@example.com" value={email} onChange={(e)=>setEmail(e.target.value)} className="input" required />
        </div>

        <div style={{marginBottom:14}}>
          <label style={{display:'block',marginBottom:6,fontSize:12,fontWeight:600,color:'var(--text-secondary)'}}>Password</label>
          <input type="password" placeholder="••••••••" value={password} onChange={(e)=>setPassword(e.target.value)} className="input" required />
        </div>

        {error && <div className="card" style={{background:'rgba(247,83,83,0.03)',borderColor:'rgba(247,83,83,0.12)',marginBottom:12}}>{error}</div>}

        <button type="submit" disabled={loading} className="btn btn-primary" style={{width:'100%'}}>{loading? 'Creating account…' : 'Create Account'}</button>
      </form>

      <div style={{textAlign:'center',marginTop:12}}>
        <span style={{color:'var(--text-secondary)'}}>Already have an account? </span>
        <button onClick={onToggle} style={{background:'none',border:'none',color:'var(--accent-purple)',cursor:'pointer'}}>Sign In</button>
      </div>
    </div>
  )
}

export default Signup