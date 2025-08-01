import React, { useState, useEffect, useCallback } from 'react';
import { Play, Pause, SkipForward, Square, AlertCircle, CheckCircle, Clock } from 'lucide-react';

interface TaskProgress {
  task_id: string;
  name: string;
  status: string;
  progress: number;
  current_step: string;
  start_time?: string;
  end_time?: string;
  error_message?: string;
  eta?: string;
  duration?: string;
}

interface RegionProgress {
  region_code: string;
  region_name: string;
  status: string;
  progress: number;
  tasks: TaskProgress[];
  start_time?: string;
  end_time?: string;
  duration?: string;
}

interface ProgressSummary {
  overall_progress: number;
  current_phase: string;
  is_paused: boolean;
  is_cancelled: boolean;
  start_time?: string;
  duration?: string;
  eta?: string;
  tasks: {
    total: number;
    completed: number;
    failed: number;
    running: number;
    pending: number;
  };
  regions: {
    total: number;
    completed: number;
    running: number;
    pending: number;
  };
  current_task?: string;
}

interface DetailedStatus {
  summary: ProgressSummary;
  tasks: Record<string, TaskProgress>;
  regions: Record<string, RegionProgress>;
}

const ProgressDashboard: React.FC = () => {
  const [status, setStatus] = useState<DetailedStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'tasks' | 'regions'>('overview');

  // Fetch progress data
  const fetchProgress = useCallback(async () => {
    try {
      const response = await fetch('/api/progress/status');
      if (!response.ok) throw new Error('Failed to fetch progress');
      const data = await response.json();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  // Control functions
  const pauseOperation = async () => {
    try {
      await fetch('/api/progress/pause', { method: 'POST' });
      fetchProgress();
    } catch (err) {
      console.error('Failed to pause operation:', err);
    }
  };

  const resumeOperation = async () => {
    try {
      await fetch('/api/progress/resume', { method: 'POST' });
      fetchProgress();
    } catch (err) {
      console.error('Failed to resume operation:', err);
    }
  };

  const skipTask = async (taskId: string) => {
    try {
      await fetch(`/api/progress/skip-task/${taskId}`, { method: 'POST' });
      fetchProgress();
    } catch (err) {
      console.error('Failed to skip task:', err);
    }
  };

  const skipRegion = async (regionCode: string) => {
    try {
      await fetch(`/api/progress/skip-region/${regionCode}`, { method: 'POST' });
      fetchProgress();
    } catch (err) {
      console.error('Failed to skip region:', err);
    }
  };

  const cancelOperation = async () => {
    if (confirm('Are you sure you want to cancel the entire operation?')) {
      try {
        await fetch('/api/progress/cancel', { method: 'POST' });
        fetchProgress();
      } catch (err) {
        console.error('Failed to cancel operation:', err);
      }
    }
  };

  // Real-time updates
  useEffect(() => {
    fetchProgress();
    const interval = setInterval(fetchProgress, 2000); // Update every 2 seconds
    return () => clearInterval(interval);
  }, [fetchProgress]);

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'running': return 'text-blue-600 bg-blue-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'paused': return 'text-yellow-600 bg-yellow-100';
      case 'skipped': return 'text-gray-600 bg-gray-100';
      case 'cancelled': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-4 h-4" />;
      case 'running': return <Clock className="w-4 h-4 animate-spin" />;
      case 'failed': return <AlertCircle className="w-4 h-4" />;
      case 'paused': return <Pause className="w-4 h-4" />;
      default: return null;
    }
  };

  const formatDuration = (duration?: string): string => {
    if (!duration) return 'N/A';
    const match = duration.match(/(\d+):(\d+):(\d+)/);
    if (match) {
      const [, hours, minutes, seconds] = match;
      return `${hours}h ${minutes}m ${seconds}s`;
    }
    return duration;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-red-800 font-medium">Error Loading Progress</h3>
        <p className="text-red-600 text-sm mt-1">{error}</p>
        <button 
          onClick={fetchProgress}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!status) return null;

  const { summary } = status;

  return (
    <div className="space-y-6">
      {/* Overall Progress Header */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Operation Progress</h1>
            <p className="text-gray-600">{summary.current_phase}</p>
          </div>
          
          {/* Control Buttons */}
          <div className="flex gap-2">
            {summary.is_paused ? (
              <button
                onClick={resumeOperation}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                <Play className="w-4 h-4" />
                Resume
              </button>
            ) : (
              <button
                onClick={pauseOperation}
                className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
              >
                <Pause className="w-4 h-4" />
                Pause
              </button>
            )}
            
            <button
              onClick={cancelOperation}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              <Square className="w-4 h-4" />
              Cancel
            </button>
          </div>
        </div>

        {/* Overall Progress Bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Overall Progress</span>
            <span className="text-sm font-bold text-gray-900">{summary.overall_progress.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className="bg-blue-600 h-3 rounded-full transition-all duration-300"
              style={{ width: `${summary.overall_progress}%` }}
            ></div>
          </div>
        </div>

        {/* Status Info */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Duration:</span>
            <span className="font-medium ml-1">{formatDuration(summary.duration)}</span>
          </div>
          <div>
            <span className="text-gray-600">ETA:</span>
            <span className="font-medium ml-1">
              {summary.eta ? new Date(summary.eta).toLocaleTimeString() : 'Calculating...'}
            </span>
          </div>
          <div>
            <span className="text-gray-600">Current Task:</span>
            <span className="font-medium ml-1">{summary.current_task || 'None'}</span>
          </div>
          <div>
            <span className="text-gray-600">Status:</span>
            <span className={`font-medium ml-1 px-2 py-1 rounded-full text-xs ${getStatusColor(summary.is_paused ? 'paused' : summary.is_cancelled ? 'cancelled' : 'running')}`}>
              {summary.is_cancelled ? 'Cancelled' : summary.is_paused ? 'Paused' : 'Running'}
            </span>
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Tasks Summary */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Tasks Summary</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Total Tasks:</span>
              <span className="font-medium">{summary.tasks.total}</span>
            </div>
            <div className="flex justify-between">
              <span>Completed:</span>
              <span className="font-medium text-green-600">{summary.tasks.completed}</span>
            </div>
            <div className="flex justify-between">
              <span>Running:</span>
              <span className="font-medium text-blue-600">{summary.tasks.running}</span>
            </div>
            <div className="flex justify-between">
              <span>Failed:</span>
              <span className="font-medium text-red-600">{summary.tasks.failed}</span>
            </div>
            <div className="flex justify-between">
              <span>Pending:</span>
              <span className="font-medium text-gray-600">{summary.tasks.pending}</span>
            </div>
          </div>
        </div>

        {/* Regions Summary */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Regions Summary</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Total Regions:</span>
              <span className="font-medium">{summary.regions.total}</span>
            </div>
            <div className="flex justify-between">
              <span>Completed:</span>
              <span className="font-medium text-green-600">{summary.regions.completed}</span>
            </div>
            <div className="flex justify-between">
              <span>Running:</span>
              <span className="font-medium text-blue-600">{summary.regions.running}</span>
            </div>
            <div className="flex justify-between">
              <span>Pending:</span>
              <span className="font-medium text-gray-600">{summary.regions.pending}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed View Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {[
              { key: 'overview', label: 'Overview' },
              { key: 'tasks', label: `Tasks (${summary.tasks.total})` },
              { key: 'regions', label: `Regions (${summary.regions.total})` }
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setSelectedTab(tab.key as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === tab.key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {selectedTab === 'overview' && (
            <div className="text-center text-gray-500">
              Select a tab above to view detailed information
            </div>
          )}

          {selectedTab === 'tasks' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">All Tasks</h3>
              {Object.values(status.tasks).map(task => (
                <div key={task.task_id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(task.status)}
                      <h4 className="font-medium">{task.name}</h4>
                      <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(task.status)}`}>
                        {task.status}
                      </span>
                    </div>
                    
                    {task.status === 'running' && (
                      <button
                        onClick={() => skipTask(task.task_id)}
                        className="flex items-center gap-1 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded"
                      >
                        <SkipForward className="w-3 h-3" />
                        Skip
                      </button>
                    )}
                  </div>

                  <div className="mb-2">
                    <div className="flex justify-between text-sm mb-1">
                      <span>{task.current_step}</span>
                      <span>{task.progress.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${task.progress}%` }}
                      ></div>
                    </div>
                  </div>

                  {task.error_message && (
                    <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                      {task.error_message}
                    </div>
                  )}

                  <div className="text-xs text-gray-500 mt-2">
                    {task.duration && `Duration: ${formatDuration(task.duration)}`}
                    {task.eta && ` | ETA: ${new Date(task.eta).toLocaleTimeString()}`}
                  </div>
                </div>
              ))}
            </div>
          )}

          {selectedTab === 'regions' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">All Regions</h3>
              {Object.values(status.regions).map(region => (
                <div key={region.region_code} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(region.status)}
                      <h4 className="font-medium">{region.region_name}</h4>
                      <span className="text-sm text-gray-500">({region.region_code})</span>
                      <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(region.status)}`}>
                        {region.status}
                      </span>
                    </div>
                    
                    {region.status !== 'completed' && region.status !== 'skipped' && (
                      <button
                        onClick={() => skipRegion(region.region_code)}
                        className="flex items-center gap-1 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded"
                      >
                        <SkipForward className="w-3 h-3" />
                        Skip Region
                      </button>
                    )}
                  </div>

                  <div className="mb-3">
                    <div className="flex justify-between text-sm mb-1">
                      <span>{region.tasks.length} tasks</span>
                      <span>{region.progress.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${region.progress}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="text-xs text-gray-500">
                    {region.duration && `Duration: ${formatDuration(region.duration)}`}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProgressDashboard;