import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  MagnifyingGlassIcon, 
  ArrowDownTrayIcon,
  EyeIcon 
} from '@heroicons/react/24/outline'
import { 
  jurisdictionsApi, 
  representativesApi, 
  billsApi,
  type Jurisdiction,
  type Representative,
  type Bill 
} from '../lib/api'

type DataType = 'jurisdictions' | 'representatives' | 'bills'

export default function Database() {
  const [activeTab, setActiveTab] = useState<DataType>('jurisdictions')
  const [searchTerm, setSearchTerm] = useState('')
  const [filters, setFilters] = useState({
    jurisdiction_type: '',
    province: '',
    party: '',
    status: '',
  })
  const [limit, setLimit] = useState(50)

  // Query based on active tab
  const { data: jurisdictions, isLoading: jurisdictionsLoading } = useQuery({
    queryKey: ['jurisdictions', filters, searchTerm, limit],
    queryFn: () => jurisdictionsApi.getJurisdictions({
      jurisdiction_type: filters.jurisdiction_type || undefined,
      province: filters.province || undefined,
      limit,
    }),
    enabled: activeTab === 'jurisdictions',
  })

  const { data: representatives, isLoading: representativesLoading } = useQuery({
    queryKey: ['representatives', filters, searchTerm, limit],
    queryFn: () => representativesApi.getRepresentatives({
      jurisdiction_type: filters.jurisdiction_type || undefined,
      province: filters.province || undefined,
      party: filters.party || undefined,
      search: searchTerm || undefined,
      limit,
    }),
    enabled: activeTab === 'representatives',
  })

  const { data: bills, isLoading: billsLoading } = useQuery({
    queryKey: ['bills', filters, searchTerm, limit],
    queryFn: () => billsApi.getBills({
      status: filters.status || undefined,
      search: searchTerm || undefined,
      limit,
    }),
    enabled: activeTab === 'bills',
  })

  const tabs = [
    { id: 'jurisdictions', name: 'Jurisdictions', count: jurisdictions?.length || 0 },
    { id: 'representatives', name: 'Representatives', count: representatives?.length || 0 },
    { id: 'bills', name: 'Bills', count: bills?.length || 0 },
  ]

  const isLoading = jurisdictionsLoading || representativesLoading || billsLoading

  const handleExport = () => {
    // Export current data as CSV
    let data: any[] = []
    let filename = ''
    
    switch (activeTab) {
      case 'jurisdictions':
        data = jurisdictions || []
        filename = 'jurisdictions.csv'
        break
      case 'representatives':
        data = representatives || []
        filename = 'representatives.csv'
        break
      case 'bills':
        data = bills || []
        filename = 'bills.csv'
        break
    }

    if (data.length === 0) return

    // Convert to CSV
    const headers = Object.keys(data[0]).join(',')
    const rows = data.map(item => 
      Object.values(item).map(value => 
        typeof value === 'string' ? `"${value.replace(/"/g, '""')}"` : value
      ).join(',')
    ).join('\n')
    
    const csv = `${headers}\n${rows}`
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Database Browser</h2>
          <p className="mt-2 text-gray-600">
            Explore and analyze Canadian civic data
          </p>
        </div>
        <button
          onClick={handleExport}
          className="btn-primary"
          disabled={isLoading}
        >
          <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
          Export
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as DataType)}
              className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.name}
              <span className="ml-2 py-0.5 px-2 rounded-full bg-gray-100 text-gray-900 text-xs">
                {tab.count}
              </span>
            </button>
          ))}
        </nav>
      </div>

      {/* Search and filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Search */}
          <div className="relative">
            <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-3 text-gray-400" />
            <input
              type="text"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10"
            />
          </div>

          {/* Jurisdiction Type Filter */}
          <select
            value={filters.jurisdiction_type}
            onChange={(e) => setFilters(prev => ({ ...prev, jurisdiction_type: e.target.value }))}
            className="select"
          >
            <option value="">All Jurisdiction Types</option>
            <option value="federal">Federal</option>
            <option value="provincial">Provincial</option>
            <option value="municipal">Municipal</option>
          </select>

          {/* Province Filter */}
          <select
            value={filters.province}
            onChange={(e) => setFilters(prev => ({ ...prev, province: e.target.value }))}
            className="select"
          >
            <option value="">All Provinces</option>
            <option value="AB">Alberta</option>
            <option value="BC">British Columbia</option>
            <option value="MB">Manitoba</option>
            <option value="NB">New Brunswick</option>
            <option value="NL">Newfoundland and Labrador</option>
            <option value="NS">Nova Scotia</option>
            <option value="ON">Ontario</option>
            <option value="PE">Prince Edward Island</option>
            <option value="QC">Quebec</option>
            <option value="SK">Saskatchewan</option>
            <option value="NT">Northwest Territories</option>
            <option value="NU">Nunavut</option>
            <option value="YT">Yukon</option>
          </select>

          {/* Results limit */}
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="select"
          >
            <option value={25}>25 results</option>
            <option value={50}>50 results</option>
            <option value={100}>100 results</option>
            <option value={200}>200 results</option>
          </select>
        </div>

        {/* Additional filters based on tab */}
        {activeTab === 'representatives' && (
          <div className="mt-4">
            <input
              type="text"
              placeholder="Filter by party..."
              value={filters.party}
              onChange={(e) => setFilters(prev => ({ ...prev, party: e.target.value }))}
              className="input max-w-xs"
            />
          </div>
        )}

        {activeTab === 'bills' && (
          <div className="mt-4">
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="select max-w-xs"
            >
              <option value="">All Statuses</option>
              <option value="introduced">Introduced</option>
              <option value="committee">In Committee</option>
              <option value="passed">Passed</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        )}
      </div>

      {/* Data table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="loading-spinner"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            {activeTab === 'jurisdictions' && (
              <JurisdictionsTable data={jurisdictions || []} />
            )}
            {activeTab === 'representatives' && (
              <RepresentativesTable data={representatives || []} />
            )}
            {activeTab === 'bills' && (
              <BillsTable data={bills || []} />
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function JurisdictionsTable({ data }: { data: Jurisdiction[] }) {
  return (
    <table className="table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Type</th>
          <th>Province</th>
          <th>Last Updated</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {data.map((jurisdiction) => (
          <tr key={jurisdiction.id}>
            <td className="font-medium">{jurisdiction.name}</td>
            <td>
              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                jurisdiction.jurisdiction_type === 'federal' ? 'bg-blue-100 text-blue-800' :
                jurisdiction.jurisdiction_type === 'provincial' ? 'bg-green-100 text-green-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {jurisdiction.jurisdiction_type}
              </span>
            </td>
            <td>{jurisdiction.province || 'N/A'}</td>
            <td>{new Date(jurisdiction.updated_at).toLocaleDateString()}</td>
            <td>
              <button className="text-primary-600 hover:text-primary-900">
                <EyeIcon className="h-4 w-4" />
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function RepresentativesTable({ data }: { data: Representative[] }) {
  return (
    <table className="table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Role</th>
          <th>Party</th>
          <th>District</th>
          <th>Contact</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {data.map((rep) => (
          <tr key={rep.id}>
            <td className="font-medium">{rep.name}</td>
            <td>{rep.role}</td>
            <td>{rep.party || 'N/A'}</td>
            <td>{rep.district || 'N/A'}</td>
            <td>
              <div className="text-sm">
                {rep.email && <div>{rep.email}</div>}
                {rep.phone && <div>{rep.phone}</div>}
              </div>
            </td>
            <td>
              <button className="text-primary-600 hover:text-primary-900">
                <EyeIcon className="h-4 w-4" />
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function BillsTable({ data }: { data: Bill[] }) {
  return (
    <table className="table">
      <thead>
        <tr>
          <th>Identifier</th>
          <th>Title</th>
          <th>Status</th>
          <th>Last Updated</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {data.map((bill) => (
          <tr key={bill.id}>
            <td className="font-medium">{bill.identifier}</td>
            <td className="max-w-xs truncate">{bill.title}</td>
            <td>
              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                bill.status === 'passed' ? 'bg-green-100 text-green-800' :
                bill.status === 'failed' ? 'bg-red-100 text-red-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {bill.status}
              </span>
            </td>
            <td>{new Date(bill.updated_at).toLocaleDateString()}</td>
            <td>
              <button className="text-primary-600 hover:text-primary-900">
                <EyeIcon className="h-4 w-4" />
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}