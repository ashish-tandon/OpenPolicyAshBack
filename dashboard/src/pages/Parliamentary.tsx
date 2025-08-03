import { useState, useEffect } from 'react'
import { parliamentaryApi, ParliamentarySession, HansardRecord, Speech, ValidationResult } from '../lib/api'
import { Search, Calendar, FileText, Users, CheckCircle, AlertCircle } from 'lucide-react'

export default function Parliamentary() {
  const [sessions, setSessions] = useState<ParliamentarySession[]>([])
  const [hansardRecords, setHansardRecords] = useState<HansardRecord[]>([])
  const [selectedHansard, setSelectedHansard] = useState<number | null>(null)
  const [speeches, setSpeeches] = useState<Speech[]>([])
  const [validationResults, setValidationResults] = useState<ValidationResult[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Speech[]>([])
  const [activeTab, setActiveTab] = useState<'hansard' | 'validation' | 'search'>('hansard')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [sessionsData, hansardData, validationData] = await Promise.all([
        parliamentaryApi.getSessions(),
        parliamentaryApi.getHansardRecords({ limit: 20 }),
        parliamentaryApi.validateFederalBills()
      ])
      setSessions(sessionsData)
      setHansardRecords(hansardData)
      setValidationResults(validationData)
    } catch (error) {
      console.error('Error loading parliamentary data:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadSpeeches = async (hansardId: number) => {
    try {
      const speechData = await parliamentaryApi.getSpeeches(hansardId)
      setSpeeches(speechData)
      setSelectedHansard(hansardId)
    } catch (error) {
      console.error('Error loading speeches:', error)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery) return
    try {
      const results = await parliamentaryApi.searchSpeeches({ 
        query: searchQuery,
        limit: 50 
      })
      setSearchResults(results)
      setActiveTab('search')
    } catch (error) {
      console.error('Error searching speeches:', error)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading parliamentary data...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Parliamentary Data</h2>
        <p className="mt-2 text-gray-600">
          Access Hansard debates, committee meetings, and speech records
        </p>
      </div>

      {/* Search Bar */}
      <div className="card">
        <div className="flex gap-4">
          <input
            type="text"
            placeholder="Search speeches, debates, and committees..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button
            onClick={handleSearch}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
          >
            <Search className="h-4 w-4" />
            Search
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('hansard')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'hansard'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <FileText className="inline h-4 w-4 mr-2" />
            Hansard Records
          </button>
          <button
            onClick={() => setActiveTab('validation')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'validation'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <CheckCircle className="inline h-4 w-4 mr-2" />
            Bill Validation
          </button>
          <button
            onClick={() => setActiveTab('search')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'search'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Search className="inline h-4 w-4 mr-2" />
            Search Results
          </button>
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'hansard' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Hansard List */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Recent Hansard Records</h3>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {hansardRecords.map((record) => (
                <div
                  key={record.id}
                  onClick={() => loadSpeeches(record.id)}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                    selectedHansard === record.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-medium flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-gray-400" />
                        {new Date(record.date).toLocaleDateString()}
                      </div>
                      {record.sitting_number && (
                        <div className="text-sm text-gray-600">
                          Sitting #{record.sitting_number}
                        </div>
                      )}
                    </div>
                    <div className="text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        record.processed 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {record.processed ? 'Processed' : 'Pending'}
                      </span>
                      {record.speech_count > 0 && (
                        <div className="text-gray-500 mt-1">
                          {record.speech_count} speeches
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Speeches */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Speeches</h3>
            {selectedHansard && speeches.length > 0 ? (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {speeches.map((speech) => (
                  <div key={speech.id} className="border-l-4 border-gray-200 pl-4">
                    <div className="font-medium text-gray-900">
                      {speech.speaker_name || 'Unknown Speaker'}
                    </div>
                    {speech.speaker_title && (
                      <div className="text-sm text-gray-600">{speech.speaker_title}</div>
                    )}
                    <p className="text-sm text-gray-700 mt-2 line-clamp-3">
                      {speech.content}
                    </p>
                    {speech.time && (
                      <div className="text-xs text-gray-500 mt-1">{speech.time}</div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">Select a Hansard record to view speeches</p>
            )}
          </div>
        </div>
      )}

      {activeTab === 'validation' && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Federal Bill Validation Results</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Bill
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quality Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Issues
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {validationResults.map((result) => (
                  <tr key={result.bill_id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {result.identifier}
                        </div>
                        <div className="text-sm text-gray-500 max-w-xs truncate">
                          {result.title}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className={`text-sm font-medium ${
                          result.quality_score >= 80 ? 'text-green-600' :
                          result.quality_score >= 60 ? 'text-yellow-600' :
                          'text-red-600'
                        }`}>
                          {result.quality_score}%
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {result.is_critical ? (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                          <AlertCircle className="h-4 w-4 mr-1" />
                          Critical
                        </span>
                      ) : (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                          Normal
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-xs text-gray-500">
                        {result.issues.length > 0 ? (
                          <ul className="list-disc list-inside">
                            {result.issues.slice(0, 2).map((issue, idx) => (
                              <li key={idx}>{issue}</li>
                            ))}
                          </ul>
                        ) : (
                          <span className="text-green-600">No issues</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'search' && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Search Results</h3>
          {searchResults.length > 0 ? (
            <div className="space-y-4">
              {searchResults.map((speech) => (
                <div key={speech.id} className="border-b border-gray-200 pb-4">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">
                        {speech.speaker_name || 'Unknown Speaker'}
                      </div>
                      {speech.speaker_title && (
                        <div className="text-sm text-gray-600">{speech.speaker_title}</div>
                      )}
                      <p className="text-sm text-gray-700 mt-2">
                        {speech.content.substring(0, 300)}...
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">
              {searchQuery ? 'No results found' : 'Enter a search query to find speeches'}
            </p>
          )}
        </div>
      )}

      {/* Session Summary */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Parliamentary Sessions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {sessions.map((session) => (
            <div key={session.id} className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Users className="h-5 w-5 text-gray-400" />
                <h4 className="font-medium">
                  {session.parliament_number}th Parliament, Session {session.session_number}
                </h4>
              </div>
              <div className="text-sm text-gray-600">
                <div>Started: {new Date(session.start_date).toLocaleDateString()}</div>
                {session.end_date && (
                  <div>Ended: {new Date(session.end_date).toLocaleDateString()}</div>
                )}
                <div className="mt-2">
                  <div>{session.hansard_records_count} Hansard records</div>
                  <div>{session.committee_meetings_count} Committee meetings</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}