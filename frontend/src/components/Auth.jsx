import React, { useState } from 'react'
import Login from './Login'
import Signup from './Signup'

const Auth = ({ onAuthSuccess }) => {
  const [isLogin, setIsLogin] = useState(true)

  const handleToggle = () => setIsLogin(!isLogin)

  return (
    <div style={{minHeight:'100vh',display:'flex',alignItems:'center',justifyContent:'center',padding:20}}>
      <div style={{width:'100%',maxWidth:420}}>
        <div style={{textAlign:'center',marginBottom:20}}>
          <div style={{width:56,height:56,margin:'0 auto 12px',borderRadius:12,display:'flex',alignItems:'center',justifyContent:'center',background:'linear-gradient(135deg, rgba(124,58,237,0.12), rgba(6,182,212,0.06))'}}>
            <span style={{fontSize:22}}>📚</span>
          </div>
          <h1 style={{fontSize:28,fontWeight:800,margin:0}}>QuizGen</h1>
          <p style={{color:'var(--text-secondary)',marginTop:6}}>AI-powered PDF quiz generator</p>
        </div>

        <div className="card">
          <div style={{display:'flex',gap:8,marginBottom:16}}>
            <button onClick={()=>setIsLogin(true)} className={`btn ${isLogin? 'btn-primary':''}`} style={{flex:1}}>{'Sign In'}</button>
            <button onClick={()=>setIsLogin(false)} className={`btn ${!isLogin? 'btn-primary':''}`} style={{flex:1}}>{'Sign Up'}</button>
          </div>

          {isLogin ? (
            <Login onSuccess={onAuthSuccess} onToggle={handleToggle} />
          ) : (
            <Signup onSuccess={onAuthSuccess} onToggle={handleToggle} />
          )}
        </div>
      </div>
    </div>
  )
}

export default Auth