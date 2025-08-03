import { useState, useEffect } from 'react'
import { representativesApi, billsApi } from '../lib/api'
import { Representative, Bill } from '../lib/api'
import { Search, User, Building, FileText, MapPin } from 'lucide-react'

interface MPPWithStats extends Representative {
  bills_count?: number
  recent_bills?: Bill[]
  photo_url?: string
}

const PROVINCES = [
  { code: 'ON', name: 'Ontario', role: 'MPP' },
  { code: 'BC', name: 'British Columbia', role: 'MLA' },
  { code: 'AB', name: 'Alberta', role: 'MLA' },
  { code: 'QC', name: 'Quebec', role: 'MNA' },
  { code: 'MB', name: 'Manitoba', role: 'MLA' },
  { code: 'SK', name: 'Saskatchewan', role: 'MLA' },
  { code: 'NS', name: 'Nova Scotia', role: 'MLA' },
  { code: 'NB', name: 'New Brunswick', role: 'MLA' },
  { code: 'NL', name: 'Newfoundland and Labrador', role: 'MHA' },
  { code: 'PE', name: 'Prince Edward Island', role: 'MLA' },
  { code: 'NT', name: 'Northwest Territories', role: 'MLA' },
  { code: 'YT', name: 'Yukon', role: 'MLA' },
  { code: 'NU', name: 'Nunavut', role: 'MLA' },
]

export default function ProvincialMPPs() {
  const [mpps, setMpps] = useState<MPPWithStats[]>([])
  const [filteredMpps, setFilteredMpps] = useState<MPPWithStats[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedProvince, setSelectedProvince] = useState('ON')
  const [searchQuery, setSearchQuery] = useState('')
  const [parties, setParties] = useState<string[]>([])
  const [selectedParty, setSelectedParty] = useState('')
  const [provincialBills, setProvincialBills] = useState<Bill[]>([])

  useEffect(() => {
    loadProvincialMPPs()
  }, [selectedProvince])

  useEffect(() => {
    filterMPPs()
  }, [mpps, searchQuery, selectedParty])

  const loadProvincialMPPs = async () => {
    try {
      setLoading(true)
      
      // Get provincial representatives for selected province
      const mppData = await representativesApi.getRepresentatives({
        province: selectedProvince,
        limit: 200
      })

      // Get provincial bills
      const bills = await billsApi.getBills({
        limit: 50
      })
      setProvincialBills(bills)

      // Extract unique parties
      const uniqueParties = [...new Set(mppData.map(mpp => mpp.party).filter(Boolean))] as string[]
      setParties(uniqueParties.sort())

      // Add bill counts (in real app, this would be optimized)
      const mppsWithStats = mppData.map(mpp => ({
        ...mpp,
        bills_count: Math.floor(Math.random() * 10), // Mock data
        recent_bills: bills.filter(b => b.jurisdiction_id === mpp.jurisdiction_id).slice(0, 3)
      }))

      setMpps(mppsWithStats)
    } catch (error) {
      console.error('Error loading provincial MPPs:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterMPPs = () => {
    let filtered = [...mpps]

    if (searchQuery) {
      filtered = filtered.filter(mpp =>
        mpp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        mpp.district?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    if (selectedParty) {
      filtered = filtered.filter(mpp => mpp.party === selectedParty)
    }

    setFilteredMpps(filtered)
  }

  const getCurrentProvince = () => PROVINCES.find(p => p.code === selectedProvince)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading provincial representatives...</div>
      </div>
    )
  }

  const currentProvince = getCurrentProvince()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Provincial Representatives</h2>
        <p className="mt-2 text-gray-600">
          Browse MPPs, MLAs, and MNAs across all Canadian provinces and territories
        </p>
      </div>

      {/* Province Selector */}
      <div className="card bg-gradient-to-r from-blue-50 to-purple-50">
        <h3 className="text-lg font-semibold mb-4">Select Province/Territory</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2">
          {PROVINCES.map((province) => (
            <button
              key={province.code}
              onClick={() => setSelectedProvince(province.code)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedProvince === province.code
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {province.code}
            </button>
          ))}
        </div>
      </div>

      {/* Current Province Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card bg-blue-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-600">{currentProvince?.name}</p>
              <p className="text-2xl font-bold text-blue-900">{filteredMpps.length} {currentProvince?.role}s</p>
            </div>
            <MapPin className="h-8 w-8 text-blue-500" />
          </div>
        </div>
        <div className="card bg-green-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-green-600">Active Bills</p>
              <p className="text-2xl font-bold text-green-900">{provincialBills.length}</p>
            </div>
            <FileText className="h-8 w-8 text-green-500" />
          </div>
        </div>
        <div className="card bg-purple-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-purple-600">Parties</p>
              <p className="text-2xl font-bold text-purple-900">{parties.length}</p>
            </div>
            <Building className="h-8 w-8 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder={`Search ${currentProvince?.name} ${currentProvince?.role}s...`}
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
        </div>
      </div>

      {/* Representatives Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredMpps.map((mpp) => (
          <div key={mpp.id} className="card hover:shadow-lg transition-shadow">
            <div className="flex items-start gap-4">
              {mpp.photo_url ? (
                <img
                  src={mpp.photo_url}
                  alt={mpp.name}
                  className="w-20 h-20 rounded-full object-cover"
                />
              ) : (
                <div className="w-20 h-20 rounded-full bg-gray-200 flex items-center justify-center">
                  <User className="h-10 w-10 text-gray-400" />
                </div>
              )}
              <div className="flex-1">
                <h3 className="text-lg font-semibold">{mpp.name}</h3>
                <p className="text-sm text-gray-600">{mpp.party}</p>
                <p className="text-sm text-gray-500">{mpp.district}</p>
                <p className="text-xs text-blue-600 mt-1">{currentProvince?.role}</p>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Sponsored Bills</span>
                <span className="text-sm text-gray-500">{mpp.bills_count || 0}</span>
              </div>
              
              {mpp.recent_bills && mpp.recent_bills.length > 0 && (
                <div className="space-y-1 mt-2">
                  {mpp.recent_bills.map((bill) => (
                    <div key={bill.id} className="text-xs">
                      <span className="font-medium">{bill.identifier}</span>
                      <span className="text-gray-500 ml-1">{bill.title.substring(0, 40)}...</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="mt-4 flex gap-2">
              <button className="flex-1 px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm">
                View Profile
              </button>
              {mpp.email && (
                <button className="px-3 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm">
                  Contact
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Recent Provincial Bills */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Recent {currentProvince?.name} Bills</h3>
        <div className="space-y-3">
          {provincialBills.slice(0, 5).map((bill) => (
            <div key={bill.id} className="flex items-start justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{bill.identifier}</span>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    bill.status === 'passed' ? 'bg-green-100 text-green-800' :
                    bill.status === 'introduced' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {bill.status}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">{bill.title}</p>
                {bill.summary && (
                  <p className="text-xs text-gray-500 mt-1">{bill.summary.substring(0, 100)}...</p>
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