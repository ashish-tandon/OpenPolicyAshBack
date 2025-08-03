import { useState, useEffect } from 'react'
import { representativesApi, billsApi } from '../lib/api'
import { Representative, Bill } from '../lib/api'
import { Search, User, Building, FileText, Users } from 'lucide-react'

interface MPWithStats extends Representative {
  bills_count?: number
  votes_count?: number
  committees_count?: number
  recent_bills?: Bill[]
  photo_url?: string
}

export default function FederalMPs() {
  const [mps, setMps] = useState<MPWithStats[]>([])
  const [filteredMps, setFilteredMps] = useState<MPWithStats[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedParty, setSelectedParty] = useState('')
  const [selectedProvince, setSelectedProvince] = useState('')
  const [parties, setParties] = useState<string[]>([])
  const [provinces, setProvinces] = useState<string[]>([])
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  useEffect(() => {
    loadFederalMPs()
  }, [])

  useEffect(() => {
    filterMPs()
  }, [mps, searchQuery, selectedParty, selectedProvince])

  const loadFederalMPs = async () => {
    try {
      setLoading(true)
      // Get all federal MPs
      const mpData = await representativesApi.getRepresentatives({
        jurisdiction_type: 'federal',
        role: 'MP',
        limit: 400
      })

      // Extract unique parties and provinces
      const uniqueParties = [...new Set(mpData.map(mp => mp.party).filter(Boolean))] as string[]
      const uniqueProvinces = [...new Set(mpData.map(mp => mp.jurisdiction?.province).filter(Boolean))] as string[]
      
      setParties(uniqueParties.sort())
      setProvinces(uniqueProvinces.sort())

      // Load additional stats for each MP (in a real app, this would be a single API call)
      const mpsWithStats = await Promise.all(
        mpData.slice(0, 20).map(async (mp) => { // Limit to 20 for demo
          try {
            const bills = await billsApi.getBills({
              jurisdiction_id: mp.jurisdiction_id,
              limit: 5
            })
            return {
              ...mp,
              bills_count: bills.length,
              recent_bills: bills.slice(0, 3),
              votes_count: Math.floor(Math.random() * 1000), // Mock data
              committees_count: Math.floor(Math.random() * 5) + 1 // Mock data
            }
          } catch {
            return mp
          }
        })
      )

      setMps(mpsWithStats)
    } catch (error) {
      console.error('Error loading federal MPs:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterMPs = () => {
    let filtered = [...mps]

    if (searchQuery) {
      filtered = filtered.filter(mp =>
        mp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        mp.district?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    if (selectedParty) {
      filtered = filtered.filter(mp => mp.party === selectedParty)
    }

    if (selectedProvince) {
      filtered = filtered.filter(mp => mp.jurisdiction?.province === selectedProvince)
    }

    setFilteredMps(filtered)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading federal MPs...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Federal Members of Parliament</h2>
        <p className="mt-2 text-gray-600">
          Browse all 338 MPs in the House of Commons with their bills, committees, and voting records
        </p>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card bg-blue-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-600">Total MPs</p>
              <p className="text-2xl font-bold text-blue-900">{mps.length}</p>
            </div>
            <User className="h-8 w-8 text-blue-500" />
          </div>
        </div>
        <div className="card bg-green-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-green-600">Parties</p>
              <p className="text-2xl font-bold text-green-900">{parties.length}</p>
            </div>
            <Users className="h-8 w-8 text-green-500" />
          </div>
        </div>
        <div className="card bg-purple-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-purple-600">Active Bills</p>
              <p className="text-2xl font-bold text-purple-900">
                {mps.reduce((sum, mp) => sum + (mp.bills_count || 0), 0)}
              </p>
            </div>
            <FileText className="h-8 w-8 text-purple-500" />
          </div>
        </div>
        <div className="card bg-orange-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-orange-600">Committees</p>
              <p className="text-2xl font-bold text-orange-900">
                {mps.reduce((sum, mp) => sum + (mp.committees_count || 0), 0)}
              </p>
            </div>
            <Building className="h-8 w-8 text-orange-500" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search by name or riding..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <select
            value={selectedParty}
            onChange={(e) => setSelectedParty(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Parties</option>
            {parties.map(party => (
              <option key={party} value={party}>{party}</option>
            ))}
          </select>
          <select
            value={selectedProvince}
            onChange={(e) => setSelectedProvince(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Provinces</option>
            {provinces.map(province => (
              <option key={province} value={province}>{province}</option>
            ))}
          </select>
        </div>
        <div className="mt-4 flex justify-between items-center">
          <p className="text-sm text-gray-600">
            Showing {filteredMps.length} of {mps.length} MPs
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-1 rounded ${viewMode === 'grid' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            >
              Grid
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1 rounded ${viewMode === 'list' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            >
              List
            </button>
          </div>
        </div>
      </div>

      {/* MPs Display */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredMps.map((mp) => (
            <div key={mp.id} className="card hover:shadow-lg transition-shadow">
              <div className="flex items-start gap-4">
                {mp.photo_url ? (
                  <img
                    src={mp.photo_url}
                    alt={mp.name}
                    className="w-20 h-20 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-20 h-20 rounded-full bg-gray-200 flex items-center justify-center">
                    <User className="h-10 w-10 text-gray-400" />
                  </div>
                )}
                <div className="flex-1">
                  <h3 className="text-lg font-semibold">{mp.name}</h3>
                  <p className="text-sm text-gray-600">{mp.party}</p>
                  <p className="text-sm text-gray-500">{mp.district}</p>
                  {mp.jurisdiction?.province && (
                    <p className="text-xs text-gray-400">{mp.jurisdiction.province}</p>
                  )}
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-2xl font-bold text-blue-600">{mp.bills_count || 0}</p>
                    <p className="text-xs text-gray-500">Bills</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-green-600">{mp.votes_count || 0}</p>
                    <p className="text-xs text-gray-500">Votes</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-purple-600">{mp.committees_count || 0}</p>
                    <p className="text-xs text-gray-500">Committees</p>
                  </div>
                </div>
              </div>

              {mp.recent_bills && mp.recent_bills.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-sm font-medium text-gray-700 mb-2">Recent Bills:</p>
                  <div className="space-y-1">
                    {mp.recent_bills.map((bill) => (
                      <div key={bill.id} className="text-xs">
                        <span className="font-medium">{bill.identifier}</span>
                        <span className="text-gray-500 ml-1">{bill.title.substring(0, 50)}...</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="mt-4 flex gap-2">
                <button className="flex-1 px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm">
                  View Profile
                </button>
                <button className="px-3 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm">
                  Contact
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  MP
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Party
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Riding
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Province
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Bills
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredMps.map((mp) => (
                <tr key={mp.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {mp.photo_url ? (
                        <img className="h-10 w-10 rounded-full" src={mp.photo_url} alt="" />
                      ) : (
                        <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                          <User className="h-5 w-5 text-gray-400" />
                        </div>
                      )}
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{mp.name}</div>
                        {mp.email && (
                          <div className="text-sm text-gray-500">{mp.email}</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                      {mp.party}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {mp.district}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {mp.jurisdiction?.province}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {mp.bills_count || 0}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button className="text-blue-600 hover:text-blue-900 mr-4">View</button>
                    <button className="text-gray-600 hover:text-gray-900">Contact</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}