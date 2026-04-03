import { Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Layout } from 'antd'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Tasks from './pages/Tasks'
import TaskDetail from './pages/TaskDetail'
import Assets from './pages/Assets'
import Resources from './pages/Resources'
import Community from './pages/Community'
import Billing from './pages/Billing'
import Header from './components/Header'
import { AuthProvider, useAuth } from './hooks/useAuth'

const { Content } = Layout

function AppContent() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>Loading...</div>
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {isAuthenticated && <Header />}
      <Content style={{ background: '#f0f2f5' }}>
        <Routes>
          <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/" />} />
          <Route path="/" element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} />
          <Route path="/tasks" element={isAuthenticated ? <Tasks /> : <Navigate to="/login" />} />
          <Route path="/tasks/:id" element={isAuthenticated ? <TaskDetail /> : <Navigate to="/login" />} />
          <Route path="/assets" element={isAuthenticated ? <Assets /> : <Navigate to="/login" />} />
          <Route path="/resources" element={isAuthenticated ? <Resources /> : <Navigate to="/login" />} />
          <Route path="/community" element={isAuthenticated ? <Community /> : <Navigate to="/login" />} />
          <Route path="/billing" element={isAuthenticated ? <Billing /> : <Navigate to="/login" />} />
        </Routes>
      </Content>
    </Layout>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App