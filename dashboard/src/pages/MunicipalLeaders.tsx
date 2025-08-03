import { useState, useEffect } from 'react'
import { representativesApi, billsApi, jurisdictionsApi } from '../lib/api'
import { Representative, Bill, Jurisdiction } from '../lib/api'
import { Search, User, Building, FileText, Users, Briefcase } from 'lucide-react'

interface LeaderWithStats extends Representative {
  bylaws_count?: number
  recent_bylaws?: Bill[]
  photo_url?: string
}

const MAJOR_CITIES = [
  { name: 'Toronto', province: 'ON' },
  { name: 'Montreal', province: 'QC' },
  { name: 'Vancouver', province: 'BC' },
  { name: 'Calgary', province: 'AB' },
  { name: 'Edmonton', province: 'AB' },
  { name: 'Ottawa', province: 'ON' },
  { name: 'Winnipeg', province: 'MB' },
  { name: 'Quebec City', province: 'QC' },
  { name: 'Hamilton', province: 'ON' },
  { name: 'Kitchener', province: 'ON' },
  { name: 'London', province: 'ON' },
  { name: 'Victoria', province: 'BC' },
  { name: 'Halifax', province: 'NS' },
  { name: 'Saskatoon', province: 'SK' },
  { name: 'Regina', province: 'SK' },
  { name: 'St. John\'s', province: 'NL' },
]

export default function MunicipalLeaders() {
  const [leaders, setLeaders] = useState<LeaderWithStats[]>([])
  const [filteredLeaders, setFilteredLeaders] = useState<LeaderWithStats[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedProvince, setSelectedProvince] = useState('')
  const [selectedRole, setSelectedRole] = useState('')
  const [municipalities, setMunicipalities] = useState<Jurisdiction[]>([])
  const [selectedMunicipality, setSelectedMunicipality] = useState('')
  const [bylaws, setBylaws] = useState<Bill[]>([])

  useEffect(() => {
    loadMunicipalData()
  }, [])

  useEffect(() => {
    filterLeaders()
  }, [leaders, searchQuery, selectedProvince, selectedRole, selectedMunicipality])

  const loadMunicipalData = async () => {
    try {
      setLoading(true)
      
      // Get municipal jurisdictions
      const munis = await jurisdictionsApi.getJurisdictions({
        limit: 100
      })
      setMunicipalities(munis)

      // Get municipal leaders
      const leaderData = await representativesApi.getRepresentatives({
        limit: 200
      })

      // Get municipal bylaws/bills
      const municipalBylaws = await billsApi.getBills({
        limit: 50
      })
      setBylaws(municipalBylaws)

      // Add stats to leaders
      const leadersWithStats = leaderData.map(leader => ({
        ...leader,
        bylaws_count: Math.floor(Math.random() * 20), // Mock data
        recent_bylaws: municipalBylaws.filter(b => b.jurisdiction_id === leader.jurisdiction_id).slice(0, 3)
      }))

      setLeaders(leadersWithStats)
    } catch (error) {
      console.error('Error loading municipal data:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterLeaders = () => {
    let filtered = [...leaders]

    if (searchQuery) {
      filtered = filtered.filter(leader =>
        leader.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        leader.district?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        leader.jurisdiction?.name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    if (selectedProvince) {
      filtered = filtered.filter(leader => leader.jurisdiction?.province === selectedProvince)
    }

    if (selectedRole) {
      filtered = filtered.filter(leader => leader.role === selectedRole)
    }

    if (selectedMunicipality) {
      filtered = filtered.filter(leader => leader.jurisdiction_id === selectedMunicipality)
    }

    setFilteredLeaders(filtered)
  }

  const getMayorCount = () => filteredLeaders.filter(l => l.role === 'Mayor').length
  const getCouncillorCount = () => filteredLeaders.filter(l => l.role === 'Councillor').length

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading municipal leaders...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Municipal Leaders</h2>
        <p className="mt-2 text-gray-600">
          Browse mayors and councillors from cities across Canada
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card bg-blue-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-600">Municipalities</p>
              <p className="text-2xl font-bold text-blue-900">{municipalities.length}</p>
            </div>
            <Building className="h-8 w-8 text-blue-500" />
          </div>
        </div>
        <div className="card bg-green-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-green-600">Mayors</p>
              <p className="text-2xl font-bold text-green-900">{getMayorCount()}</p>
            </div>
            <Briefcase className="h-8 w-8 text-green-500" />
          </div>
        </div>
        <div className="card bg-purple-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-purple-600">Councillors</p>
              <p className="text-2xl font-bold text-purple-900">{getCouncillorCount()}</p>
            </div>
            <Users className="h-8 w-8 text-purple-500" />
          </div>
        </div>
        <div className="card bg-orange-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-orange-600">Bylaws</p>
              <p className="text-2xl font-bold text-orange-900">{bylaws.length}</p>
            </div>
            <FileText className="h-8 w-8 text-orange-500" />
          </div>
        </div>
      </div>

      {/* Quick Access to Major Cities */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Major Cities</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2">
          {MAJOR_CITIES.map((city) => (
            <button
              key={city.name}
              onClick={() => {
                const muni = municipalities.find(m => m.name.includes(city.name))
                if (muni) setSelectedMunicipality(muni.id)
              }}
              className="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              {city.name}
            </button>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search leaders or cities..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <select
            value={selectedMunicipality}
            onChange={(e) => setSelectedMunicipality(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Municipalities</option>
            {municipalities.map(muni => (
              <option key={muni.id} value={muni.id}>
                {muni.name} {muni.province && `(${muni.province})`}
              </option>
            ))}
          </select>
          <select
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Roles</option>
            <option value="Mayor">Mayors Only</option>
            <option value="Councillor">Councillors Only</option>
          </select>
          <select
            value={selectedProvince}
            onChange={(e) => setSelectedProvince(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Provinces</option>
            <option value="ON">Ontario</option>
            <option value="QC">Quebec</option>
            <option value="BC">British Columbia</option>
            <option value="AB">Alberta</option>
            <option value="MB">Manitoba</option>
            <option value="SK">Saskatchewan</option>
            <option value="NS">Nova Scotia</option>
            <option value="NB">New Brunswick</option>
            <option value="NL">Newfoundland</option>
            <option value="PE">PEI</option>
          </select>
        </div>
      </div>

      {/* Leaders Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredLeaders.map((leader) => (
          <div key={leader.id} className="card hover:shadow-lg transition-shadow">
            <div className="flex items-start gap-4">
              {leader.photo_url ? (
                <img
                  src={leader.photo_url}
                  alt={leader.name}
                  className="w-20 h-20 rounded-full object-cover"
                />
              ) : (
                <div className="w-20 h-20 rounded-full bg-gray-200 flex items-center justify-center">
                  <User className="h-10 w-10 text-gray-400" />
                </div>
              )}
              <div className="flex-1">
                <h3 className="text-lg font-semibold">{leader.name}</h3>
                <p className="text-sm font-medium text-blue-600">{leader.role}</p>
                <p className="text-sm text-gray-600">{leader.jurisdiction?.name}</p>
                {leader.district && (
                  <p className="text-sm text-gray-500">{leader.district}</p>
                )}
                {leader.jurisdiction?.province && (
                  <p className="text-xs text-gray-400">{leader.jurisdiction.province}</p>
                )}
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Bylaws/Resolutions</span>
                <span className="text-sm text-gray-500">{leader.bylaws_count || 0}</span>
              </div>
              
              {leader.recent_bylaws && leader.recent_bylaws.length > 0 && (
                <div className="space-y-1 mt-2">
                  {leader.recent_bylaws.map((bylaw) => (
                    <div key={bylaw.id} className="text-xs">
                      <span className="font-medium">{bylaw.identifier}</span>
                      <span className="text-gray-500 ml-1">{bylaw.title.substring(0, 40)}...</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="mt-4 flex gap-2">
              <button className="flex-1 px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm">
                View Profile
              </button>
              {leader.email && (
                <button className="px-3 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm">
                  Contact
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Recent Bylaws */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Recent Municipal Bylaws & Resolutions</h3>
        <div className="space-y-3">
          {bylaws.slice(0, 5).map((bylaw) => (
            <div key={bylaw.id} className="flex items-start justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{bylaw.identifier}</span>
                  <span className="text-sm text-gray-600">• {bylaw.jurisdiction?.name}</span>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    bylaw.status === 'passed' ? 'bg-green-100 text-green-800' :
                    bylaw.status === 'introduced' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {bylaw.status}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">{bylaw.title}</p>
                {bylaw.summary && (
                  <p className="text-xs text-gray-500 mt-1">{bylaw.summary.substring(0, 100)}...</p>
                )}
              </div>
              <button className="ml-4 text-blue-600 hover:text-blue-800 text-sm">
                View Details
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}