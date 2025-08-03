import { useQuery } from '@tanstack/react-query'
import { 
  PieChart, 
  Pie, 
  Cell, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts'
import { 
  UsersIcon, 
  BuildingOfficeIcon, 
  DocumentTextIcon, 
  CheckCircleIcon 
} from '@heroicons/react/24/outline'
import { statsApi, jurisdictionsApi, representativesApi, billsApi } from '../lib/api'

// Color palette for charts

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: statsApi.getStats,
  })

  const { data: jurisdictions } = useQuery({
    queryKey: ['jurisdictions-sample'],
    queryFn: () => jurisdictionsApi.getJurisdictions({ limit: 10 }),
  })

  const { data: representatives } = useQuery({
    queryKey: ['representatives-sample'],
    queryFn: () => representativesApi.getRepresentatives({ limit: 10, jurisdiction_type: 'federal' }),
  })

  const { data: bills } = useQuery({
    queryKey: ['bills-sample'],
    queryFn: () => billsApi.getBills({ limit: 10 }),
  })

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner"></div>
      </div>
    )
  }

  const jurisdictionData = stats ? [
    { name: 'Federal', value: stats.federal_jurisdictions, color: '#3b82f6' },
    { name: 'Provincial', value: stats.provincial_jurisdictions, color: '#10b981' },
    { name: 'Municipal', value: stats.municipal_jurisdictions, color: '#f59e0b' },
  ] : []

  const representativeData = stats ? [
    { name: 'MPs', count: stats.representatives_mp || 0 },
    { name: 'MPPs/MLAs', count: (stats.representatives_mpp || 0) + (stats.representatives_mla || 0) },
    { name: 'Mayors', count: stats.representatives_mayor || 0 },
    { name: 'Councillors', count: stats.representatives_councillor || 0 },
  ] : []

  const statCards = [
    {
      title: 'Total Jurisdictions',
      value: stats?.total_jurisdictions || 0,
      icon: BuildingOfficeIcon,
      color: 'bg-blue-500',
      change: '+12% from last month',
    },
    {
      title: 'Representatives',
      value: stats?.total_representatives || 0,
      icon: UsersIcon,
      color: 'bg-green-500',
      change: '+5% from last month',
    },
    {
      title: 'Bills Tracked',
      value: stats?.total_bills || 0,
      icon: DocumentTextIcon,
      color: 'bg-yellow-500',
      change: '+23% from last month',
    },
    {
      title: 'System Health',
      value: '99.9%',
      icon: CheckCircleIcon,
      color: 'bg-emerald-500',
      change: 'All systems operational',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h2 className="text-3xl font-bold leading-tight text-gray-900">Dashboard Overview</h2>
        <p className="mt-2 text-gray-600">
          Real-time monitoring of Canadian civic data collection and processing
        </p>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card) => (
          <div key={card.title} className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className={`p-3 rounded-lg ${card.color}`}>
                  <card.icon className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-4 flex-1">
                <div className="text-sm font-medium text-gray-500">{card.title}</div>
                <div className="text-2xl font-semibold text-gray-900">
                  {typeof card.value === 'number' ? card.value.toLocaleString() : card.value}
                </div>
                <div className="text-sm text-gray-500">{card.change}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Jurisdictions distribution */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Jurisdictions by Type</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={jurisdictionData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {jurisdictionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Representatives by role */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Representatives by Role</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={representativeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent data */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent jurisdictions */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Jurisdictions</h3>
          <div className="space-y-3">
            {jurisdictions?.slice(0, 5).map((jurisdiction) => (
              <div key={jurisdiction.id} className="flex items-center space-x-3">
                <div className={`h-2 w-2 rounded-full ${
                  jurisdiction.jurisdiction_type === 'federal' ? 'bg-blue-500' :
                  jurisdiction.jurisdiction_type === 'provincial' ? 'bg-green-500' : 'bg-yellow-500'
                }`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {jurisdiction.name}
                  </p>
                  <p className="text-sm text-gray-500 capitalize">
                    {jurisdiction.jurisdiction_type}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent representatives */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Federal MPs</h3>
          <div className="space-y-3">
            {representatives?.slice(0, 5).map((rep) => (
              <div key={rep.id} className="flex items-center space-x-3">
                <div className="h-8 w-8 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="text-xs font-medium text-primary-700">
                    {rep.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {rep.name}
                  </p>
                  <p className="text-sm text-gray-500">
                    {rep.party} • {rep.district}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent bills */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Bills</h3>
          <div className="space-y-3">
            {bills?.slice(0, 5).map((bill) => (
              <div key={bill.id} className="space-y-1">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {bill.identifier}
                </p>
                <p className="text-sm text-gray-600 line-clamp-2">
                  {bill.title}
                </p>
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    bill.status === 'passed' ? 'bg-green-100 text-green-800' :
                    bill.status === 'failed' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {bill.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}