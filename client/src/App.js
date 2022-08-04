import React from 'react';
import './App.css';
import { Login } from './components/Login';
import { CodePage } from './components/CodePage';
import { Dashboard } from './components/Dashboard';
import { BrowserRouter, Routes, Route } from 'react-router-dom';


function App() {

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/code_page" element={<CodePage />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>


    // {/* <div className="App">
    //   <Login />
    // </div> */}
  );
}

export default App;
