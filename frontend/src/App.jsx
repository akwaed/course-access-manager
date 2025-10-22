import React, { useState } from 'react';
import CourseAccessManager from './components/CourseAccessManager';
import Login from './components/Login';
import './App.css';

function App() {
  const [user, setUser] = useState(null);

  const handleLogout = () => {
    setUser(null);
  };

  if (!user) {
    return <Login onLogin={setUser} />;
  }

  return (
    <div className="App">
      <CourseAccessManager user={user} onLogout={handleLogout} />
    </div>
  );
}

export default App;
