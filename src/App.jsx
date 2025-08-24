import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AppShell from './components/layout/AppShell.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Cameras from './pages/Cameras.jsx'
import Realtime from './pages/Realtime.jsx'
import Logs from './pages/Logs.jsx'
import MissingPeople from './pages/MissingPeople.jsx'
import Settings from './pages/Settings.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/cameras" element={<Cameras />} />
          <Route path="/realtime" element={<Realtime />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/missing" element={<MissingPeople />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}