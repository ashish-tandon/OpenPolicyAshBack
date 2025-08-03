import { useState, useEffect } from 'react'
import { Key, Shield, Users, Server, Database, Activity } from 'lucide-react'
import { api } from '../lib/api'

interface ApiKey {
  id: string
  key: string
  name: string
  role: 'admin' | 'government' | 'researcher' | 'journalist' | 'public'
  created_at: string
  last_used?: string
  requests_count: number
}

interface SystemHealth {
  api: { status: string; response_time: number }
  database: { status: string; connections: number }
  redis: { status: string; memory_used: string }
  opa: { status: string; version?: string }
}

export default function Admin() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [adminPassword, setAdminPassword] = useState('')
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null)
  const [newApiKey, setNewApiKey] = useState({ name: '', role: 'public' })
  const [activeTab, setActiveTab] = useState<'keys' | 'users' | 'system'>('keys')

  useEffect(() => {
    // Check if already authenticated
    const token = localStorage.getItem('admin_token')
    if (token) {
      setIsAuthenticated(true)
      loadAdminData()
    }
  }, [])

  const handleLogin = () => {
    // Simple password check - in production, this should be a proper auth endpoint
    if (adminPassword === 'admin123') { // TODO: Replace with secure authentication
      localStorage.setItem('admin_token', 'dummy_token')
      setIsAuthenticated(true)
      loadAdminData()
    } else {
      alert('Invalid password')
    }
  }

  const loadAdminData = async () => {
    try {
      // Load API keys (mock data for now)
      const mockApiKeys: ApiKey[] = [
        {
          id: '1',
          key: 'govt_key_123abc',
          name: 'Government Portal',
          role: 'government',
          created_at: '2024-01-15',
          last_used: '2024-01-20',
          requests_count: 45678
        },
        {
          id: '2',
          key: 'research_key_456def',
          name: 'University Research Team',
          role: 'researcher',
          created_at: '2024-01-10',
          last_used: '2024-01-19',
          requests_count: 12345
        }
      ]
      setApiKeys(mockApiKeys)

      // Load system health
      const health: SystemHealth = {
        api: { status: 'healthy', response_time: 45 },
        database: { status: 'healthy', connections: 12 },
        redis: { status: 'healthy', memory_used: '256MB' },
        opa: { status: 'healthy', version: '0.58.0' }
      }
      setSystemHealth(health)
    } catch (error) {
      console.error('Error loading admin data:', error)
    }
  }

  const generateApiKey = () => {
    const key = `${newApiKey.role}_${Math.random().toString(36).substring(2, 15)}`
    const newKey: ApiKey = {
      id: Date.now().toString(),
      key,
      name: newApiKey.name,
      role: newApiKey.role as ApiKey['role'],
      created_at: new Date().toISOString().split('T')[0],
      requests_count: 0
    }
    setApiKeys([...apiKeys, newKey])
    setNewApiKey({ name: '', role: 'public' })
  }

  const deleteApiKey = (id: string) => {
    setApiKeys(apiKeys.filter(key => key.id !== id))
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full space-y-8">
          <div>
            <div className="mx-auto h-12 w-12 bg-blue-600 rounded-lg flex items-center justify-center">
              <Shield className="h-8 w-8 text-white" />
            </div>
            <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
              Admin Access
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              Enter admin password to continue
            </p>
          </div>
          <div className="mt-8 space-y-6">
            <div>
              <input
                type="password"
                value={adminPassword}
                onChange={(e) => setAdminPassword(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Admin password"
              />
            </div>
            <div>
              <button
                onClick={handleLogin}
                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Sign in
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Admin Panel</h2>
        <p className="mt-2 text-gray-600">
          Manage API keys, users, and system configuration
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('keys')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'keys'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Key className="inline h-4 w-4 mr-2" />
            API Keys
          </button>
          <button
            onClick={() => setActiveTab('users')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'users'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Users className="inline h-4 w-4 mr-2" />
            Users
          </button>
          <button
            onClick={() => setActiveTab('system')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'system'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Server className="inline h-4 w-4 mr-2" />
            System
          </button>
        </nav>
      </div>

      {/* API Keys Tab */}
      {activeTab === 'keys' && (
        <div className="space-y-6">
          {/* Create New API Key */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Create New API Key</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <input
                type="text"
                placeholder="Key name/description"
                value={newApiKey.name}
                onChange={(e) => setNewApiKey({ ...newApiKey, name: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
              <select
                value={newApiKey.role}
                onChange={(e) => setNewApiKey({ ...newApiKey, role: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="public">Public</option>
                <option value="researcher">Researcher</option>
                <option value="journalist">Journalist</option>
                <option value="government">Government</option>
                <option value="admin">Admin</option>
              </select>
              <button
                onClick={generateApiKey}
                disabled={!newApiKey.name}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                Generate Key
              </button>
            </div>
          </div>

          {/* API Keys List */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Active API Keys</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Key
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Role
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Usage
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {apiKeys.map((apiKey) => (
                    <tr key={apiKey.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {apiKey.name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                          {apiKey.key}
                        </code>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          apiKey.role === 'admin' ? 'bg-red-100 text-red-800' :
                          apiKey.role === 'government' ? 'bg-purple-100 text-purple-800' :
                          apiKey.role === 'researcher' ? 'bg-blue-100 text-blue-800' :
                          apiKey.role === 'journalist' ? 'bg-green-100 text-green-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {apiKey.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div>{apiKey.requests_count.toLocaleString()} requests</div>
                        {apiKey.last_used && (
                          <div className="text-xs">Last: {apiKey.last_used}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => deleteApiKey(apiKey.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Users Tab */}
      {activeTab === 'users' && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">User Management</h3>
          <p className="text-gray-600">
            User management interface will be implemented here. This will include:
          </p>
          <ul className="mt-4 list-disc list-inside text-gray-600 space-y-2">
            <li>User registration and authentication</li>
            <li>Role-based access control</li>
            <li>Usage quotas and limits</li>
            <li>Activity monitoring</li>
          </ul>
        </div>
      )}

      {/* System Tab */}
      {activeTab === 'system' && systemHealth && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {Object.entries(systemHealth).map(([service, health]) => (
              <div key={service} className="card">
                <div className="flex items-center justify-between">
                  <h4 className="text-lg font-semibold capitalize">{service}</h4>
                  <div className={`h-3 w-3 rounded-full ${
                    health.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                </div>
                <div className="mt-2 text-sm text-gray-600">
                  <div>Status: {health.status}</div>
                  {service === 'api' && 'response_time' in health && (
                    <div>Response: {health.response_time}ms</div>
                  )}
                  {service === 'database' && 'connections' in health && (
                    <div>Connections: {health.connections}</div>
                  )}
                  {service === 'redis' && 'memory_used' in health && (
                    <div>Memory: {health.memory_used}</div>
                  )}
                  {service === 'opa' && health.version && (
                    <div>Version: {health.version}</div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold mb-4">System Actions</h3>
            <div className="space-y-4">
              <button className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600">
                <Database className="inline h-4 w-4 mr-2" />
                Run Database Migration
              </button>
              <button className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 ml-4">
                <Activity className="inline h-4 w-4 mr-2" />
                Clear Redis Cache
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}