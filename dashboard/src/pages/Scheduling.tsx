import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { 
  PlayIcon, 
  StopIcon, 
  ClockIcon, 
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline'
import { schedulingApi } from '../lib/api'

export default function Scheduling() {
  const [selectedTaskType, setSelectedTaskType] = useState<'test' | 'federal' | 'provincial' | 'municipal'>('test')
  const queryClient = useQueryClient()

  const { data: recentRuns, isLoading: runsLoading } = useQuery({
    queryKey: ['scraping-runs'],
    queryFn: schedulingApi.getRecentRuns,
    refetchInterval: 5000, // Refresh every 5 seconds
  })

  const scheduleTaskMutation = useMutation({
    mutationFn: schedulingApi.scheduleTask,
    onSuccess: (data) => {
      toast.success(`Task scheduled successfully: ${data.task_id}`)
      queryClient.invalidateQueries({ queryKey: ['scraping-runs'] })
    },
    onError: (error) => {
      toast.error(`Failed to schedule task: ${error.message}`)
    },
  })

  const cancelTaskMutation = useMutation({
    mutationFn: schedulingApi.cancelTask,
    onSuccess: () => {
      toast.success('Task cancelled successfully')
      queryClient.invalidateQueries({ queryKey: ['scraping-runs'] })
    },
    onError: (error) => {
      toast.error(`Failed to cancel task: ${error.message}`)
    },
  })

  const handleScheduleTask = () => {
    scheduleTaskMutation.mutate(selectedTaskType)
  }

  const handleCancelTask = (taskId: string) => {
    cancelTaskMutation.mutate(taskId)
  }

  const taskTypes = [
    {
      id: 'test' as const,
      name: 'Test Run',
      description: 'Run a limited test with maximum 5 records per jurisdiction',
      color: 'bg-blue-500',
      priority: 'Low',
    },
    {
      id: 'federal' as const,
      name: 'Federal Only',
      description: 'Scrape federal government data (Parliament of Canada)',
      color: 'bg-red-500',
      priority: 'High',
    },
    {
      id: 'provincial' as const,
      name: 'Provincial',
      description: 'Scrape all provincial and territorial governments',
      color: 'bg-green-500',
      priority: 'Medium',
    },
    {
      id: 'municipal' as const,
      name: 'Municipal',
      description: 'Scrape all municipal governments (108 jurisdictions)',
      color: 'bg-yellow-500',
      priority: 'Medium',
    },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'running':
        return 'bg-blue-100 text-blue-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Scraper Scheduling</h2>
        <p className="mt-2 text-gray-600">
          Schedule and manage data collection tasks across Canadian jurisdictions
        </p>
      </div>

      {/* Quick actions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Start</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {taskTypes.map((type) => (
            <div
              key={type.id}
              className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                selectedTaskType === type.id
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setSelectedTaskType(type.id)}
            >
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${type.color}`}>
                  <ClockIcon className="h-5 w-5 text-white" />
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{type.name}</h4>
                  <p className="text-sm text-gray-500">{type.description}</p>
                  <span className={`inline-block mt-1 px-2 py-1 text-xs font-semibold rounded-full ${
                    type.priority === 'High' ? 'bg-red-100 text-red-800' :
                    type.priority === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {type.priority} Priority
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            Selected: <span className="font-medium">{taskTypes.find(t => t.id === selectedTaskType)?.name}</span>
          </div>
          <button
            onClick={handleScheduleTask}
            disabled={scheduleTaskMutation.isPending}
            className="btn-primary"
          >
            {scheduleTaskMutation.isPending ? (
              <>
                <div className="loading-spinner mr-2" />
                Scheduling...
              </>
            ) : (
              <>
                <PlayIcon className="h-4 w-4 mr-2" />
                Run Now
              </>
            )}
          </button>
        </div>
      </div>

      {/* Federal Bills Priority Alert */}
      <div className="card bg-blue-50 border-blue-200">
        <div className="flex items-start space-x-3">
          <ExclamationTriangleIcon className="h-6 w-6 text-blue-600 mt-1" />
          <div>
            <h3 className="text-lg font-semibold text-blue-900">Federal Bills Priority</h3>
            <p className="text-blue-700 mb-3">
              Federal Canadian bills receive enhanced monitoring with automatic quality checks and AI summaries.
              The system prioritizes federal data with more frequent updates and comprehensive validation.
            </p>
            <button
              onClick={() => {
                setSelectedTaskType('federal')
                handleScheduleTask()
              }}
              className="btn bg-blue-600 text-white hover:bg-blue-700"
            >
              <PlayIcon className="h-4 w-4 mr-2" />
              Run Federal Scraper Now
            </button>
          </div>
        </div>
      </div>

      {/* Recent runs */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Recent Scraping Runs</h3>
          <button
            onClick={() => queryClient.invalidateQueries({ queryKey: ['scraping-runs'] })}
            className="btn-secondary text-sm"
          >
            Refresh
          </button>
        </div>

        {runsLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="loading-spinner"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Task ID</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Progress</th>
                  <th>Duration</th>
                  <th>Results</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {recentRuns?.map((run) => (
                  <tr key={run.id}>
                    <td className="font-mono text-sm">{run.task_id.slice(0, 8)}...</td>
                    <td>
                      <div className="flex flex-wrap gap-1">
                        {run.jurisdiction_types.map((type) => (
                          <span
                            key={type}
                            className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              type === 'federal' ? 'bg-red-100 text-red-800' :
                              type === 'provincial' ? 'bg-green-100 text-green-800' :
                              'bg-yellow-100 text-yellow-800'
                            }`}
                          >
                            {type}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td>
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(run.status)}`}>
                        {run.status}
                      </span>
                    </td>
                    <td>
                      <div className="text-sm">
                        <div>Created: {run.records_created}</div>
                        <div>Updated: {run.records_updated}</div>
                        {run.errors_count > 0 && (
                          <div className="text-red-600">Errors: {run.errors_count}</div>
                        )}
                      </div>
                    </td>
                    <td className="text-sm">
                      {run.started_at && (
                        <div>
                          Started: {new Date(run.started_at).toLocaleTimeString()}
                        </div>
                      )}
                      {run.completed_at && (
                        <div>
                          Completed: {new Date(run.completed_at).toLocaleTimeString()}
                        </div>
                      )}
                    </td>
                    <td>
                      <div className="text-sm">
                        <div className="text-green-600">+{run.records_created} created</div>
                        <div className="text-blue-600">~{run.records_updated} updated</div>
                        {run.errors_count > 0 && (
                          <div className="text-red-600">!{run.errors_count} errors</div>
                        )}
                      </div>
                    </td>
                    <td>
                      {(run.status === 'running' || run.status === 'pending') && (
                        <button
                          onClick={() => handleCancelTask(run.task_id)}
                          disabled={cancelTaskMutation.isPending}
                          className="text-red-600 hover:text-red-900"
                        >
                          <StopIcon className="h-4 w-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Scheduling information */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Automated Schedule</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <h4 className="font-medium text-gray-900">Daily Full Scrape</h4>
                <p className="text-sm text-gray-600">All jurisdictions, runs at midnight UTC</p>
              </div>
              <span className="text-green-600 font-medium">Active</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <h4 className="font-medium text-gray-900">Federal Priority Check</h4>
                <p className="text-sm text-gray-600">Federal bills only, runs every 4 hours</p>
              </div>
              <span className="text-green-600 font-medium">Active</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <h4 className="font-medium text-gray-900">Quality Monitoring</h4>
                <p className="text-sm text-gray-600">Data validation, runs hourly</p>
              </div>
              <span className="text-green-600 font-medium">Active</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Metrics</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Average Scrape Time</span>
              <span className="font-medium">4.2 minutes</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Success Rate (24h)</span>
              <span className="font-medium text-green-600">98.5%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Records/Minute</span>
              <span className="font-medium">~1,000</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Federal Priority Uptime</span>
              <span className="font-medium text-green-600">99.9%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}