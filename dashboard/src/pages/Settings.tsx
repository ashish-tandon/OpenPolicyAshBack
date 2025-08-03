import { useState, useEffect } from 'react'
import { Shield, AlertCircle, CheckCircle, Settings as SettingsIcon, Database, Globe, Key } from 'lucide-react'
import { parliamentaryApi } from '../lib/api'

interface PolicyHealth {
  status: string
  opa_version?: string
  policies_loaded?: number
  last_evaluation?: string
}

interface PolicyConfig {
  rate_limits: {
    anonymous: number
    authenticated: number
    government: number
  }
  quality_thresholds: {
    minimum_score: number
    critical_keywords: string[]
  }
}

export default function Settings() {
  const [policyHealth, setPolicyHealth] = useState<PolicyHealth | null>(null)
  const [policyConfig, setPolicyConfig] = useState<PolicyConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'policy' | 'database' | 'api'>('policy')

  useEffect(() => {
    loadPolicyData()
  }, [])

  const loadPolicyData = async () => {
    try {
      setLoading(true)
      const health = await parliamentaryApi.getPolicyHealth()
      setPolicyHealth({
        status: health.status,
        opa_version: health.opa_version,
        policies_loaded: 2,
        last_evaluation: new Date().toISOString()
      })

      // Mock config data
      setPolicyConfig({
        rate_limits: {
          anonymous: 1000,
          authenticated: 5000,
          government: 50000
        },
        quality_thresholds: {
          minimum_score: 60,
          critical_keywords: ['budget', 'tax', 'healthcare', 'emergency', 'climate']
        }
      })
    } catch (error) {
      console.error('Error loading policy data:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Settings</h2>
        <p className="mt-2 text-gray-600">
          Configure system settings and policy engine
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('policy')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'policy'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Shield className="inline h-4 w-4 mr-2" />
            Policy Engine
          </button>
          <button
            onClick={() => setActiveTab('database')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'database'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Database className="inline h-4 w-4 mr-2" />
            Database
          </button>
          <button
            onClick={() => setActiveTab('api')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'api'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Globe className="inline h-4 w-4 mr-2" />
            API Settings
          </button>
        </nav>
      </div>

      {/* Policy Engine Tab */}
      {activeTab === 'policy' && (
        <div className="space-y-6">
          {/* Policy Engine Status */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Open Policy Agent Status
            </h3>
            {loading ? (
              <div className="text-gray-500">Loading policy engine status...</div>
            ) : policyHealth ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Status</span>
                  <div className="flex items-center gap-2">
                    {policyHealth.status === 'healthy' ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-red-500" />
                    )}
                    <span className={policyHealth.status === 'healthy' ? 'text-green-600' : 'text-red-600'}>
                      {policyHealth.status === 'healthy' ? 'Healthy' : 'Unhealthy'}
                    </span>
                  </div>
                </div>
                {policyHealth.opa_version && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">OPA Version</span>
                    <span className="font-mono text-sm">{policyHealth.opa_version}</span>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Policies Loaded</span>
                  <span>{policyHealth.policies_loaded} policies</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Last Evaluation</span>
                  <span className="text-sm text-gray-500">
                    {policyHealth.last_evaluation ? new Date(policyHealth.last_evaluation).toLocaleString() : 'Never'}
                  </span>
                </div>
              </div>
            ) : (
              <div className="text-red-600 flex items-center gap-2">
                <AlertCircle className="h-5 w-5" />
                Failed to load policy engine status
              </div>
            )}
          </div>

          {/* Rate Limits Configuration */}
          {policyConfig && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Rate Limits</h3>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Anonymous Users
                    </label>
                    <input
                      type="number"
                      value={policyConfig.rate_limits.anonymous}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      readOnly
                    />
                    <p className="text-xs text-gray-500 mt-1">requests per hour</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Authenticated Users
                    </label>
                    <input
                      type="number"
                      value={policyConfig.rate_limits.authenticated}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      readOnly
                    />
                    <p className="text-xs text-gray-500 mt-1">requests per hour</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Government Users
                    </label>
                    <input
                      type="number"
                      value={policyConfig.rate_limits.government}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      readOnly
                    />
                    <p className="text-xs text-gray-500 mt-1">requests per hour</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Quality Thresholds */}
          {policyConfig && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Quality Thresholds</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Minimum Quality Score
                  </label>
                  <input
                    type="number"
                    value={policyConfig.quality_thresholds.minimum_score}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    readOnly
                  />
                  <p className="text-xs text-gray-500 mt-1">Bills below this score are flagged for review</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Critical Keywords
                  </label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {policyConfig.quality_thresholds.critical_keywords.map((keyword) => (
                      <span
                        key={keyword}
                        className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Bills containing these keywords are marked as critical</p>
                </div>
              </div>
            </div>
          )}

          {/* Policy Files */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Policy Files</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <SettingsIcon className="h-5 w-5 text-gray-500" />
                  <div>
                    <div className="font-medium">data_quality.rego</div>
                    <div className="text-sm text-gray-500">Data validation and quality scoring policies</div>
                  </div>
                </div>
                <span className="text-sm text-green-600">Active</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Key className="h-5 w-5 text-gray-500" />
                  <div>
                    <div className="font-medium">api_access.rego</div>
                    <div className="text-sm text-gray-500">API access control and rate limiting policies</div>
                  </div>
                </div>
                <span className="text-sm text-green-600">Active</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Database Tab */}
      {activeTab === 'database' && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Database Configuration</h3>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Host</label>
                <input
                  type="text"
                  value="postgres"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  readOnly
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Port</label>
                <input
                  type="text"
                  value="5432"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  readOnly
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Database</label>
                <input
                  type="text"
                  value="opencivicdata"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  readOnly
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">User</label>
                <input
                  type="text"
                  value="openpolicy"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  readOnly
                />
              </div>
            </div>
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                Database configuration is managed through environment variables. 
                Update the docker-compose.yml file to change settings.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* API Settings Tab */}
      {activeTab === 'api' && (
        <div className="space-y-6">
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">API Configuration</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
                <input
                  type="text"
                  value="http://localhost:8000"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  readOnly
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">CORS Origins</label>
                <input
                  type="text"
                  value="*"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  readOnly
                />
                <p className="text-xs text-gray-500 mt-1">Configure specific origins in production</p>
              </div>
            </div>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold mb-4">API Documentation</h3>
            <div className="space-y-2">
              <a
                href="/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="font-medium text-blue-600">Swagger UI</div>
                <div className="text-sm text-gray-500">Interactive API documentation</div>
              </a>
              <a
                href="/redoc"
                target="_blank"
                rel="noopener noreferrer"
                className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="font-medium text-blue-600">ReDoc</div>
                <div className="text-sm text-gray-500">Alternative API documentation</div>
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}