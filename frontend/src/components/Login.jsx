import React, { useState } from 'react';
import { UK_COLORS } from '../utils/constants';

const Login = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();

    // For now, check against fallback admin
    if (email === 'admin@uky.edu' && password === 'UK2024Admin!') {
      onLogin({
        email,
        role: 'System Admin',
        first_name: 'Admin',
        last_name: 'User'
      });
    } else {
      setError('Invalid credentials');
    }
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      backgroundColor: '#f8f9fa'
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '2rem',
        borderRadius: '8px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        width: '100%',
        maxWidth: '400px'
      }}>
        <div style={{
          backgroundColor: UK_COLORS.wildcatBlue,
          color: 'white',
          padding: '1rem',
          margin: '-2rem -2rem 2rem -2rem',
          borderRadius: '8px 8px 0 0',
          textAlign: 'center'
        }}>
          <h2>TCE Contacts Manager</h2>
          <p>University of Kentucky</p>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem' }}>
              Email:
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #ddd',
                borderRadius: '4px'
              }}
              required
            />
          </div>
          
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem' }}>
              Password:
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #ddd',
                borderRadius: '4px'
              }}
              required
            />
          </div>
          
          {error && (
            <div style={{ 
              color: 'red', 
              marginBottom: '1rem',
              fontSize: '0.9rem'
            }}>
              {error}
            </div>
          )}
          
          <button
            type="submit"
            style={{
              width: '100%',
              padding: '0.75rem',
              backgroundColor: UK_COLORS.wildcatBlue,
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '1rem'
            }}
          >
            Login
          </button>
        </form>
        
        <div style={{
          marginTop: '2rem',
          padding: '1rem',
          backgroundColor: '#f0f0f0',
          borderRadius: '4px',
          fontSize: '0.9rem'
        }}>
          <strong>Admin Access:</strong><br/>
          Email: admin@uky.edu<br/>
          Password: UK2024Admin!
        </div>
      </div>
    </div>
  );
};

export default Login;
