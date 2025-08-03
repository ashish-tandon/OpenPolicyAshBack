import React, { useState } from 'react';
import { Database, Download, Settings } from 'lucide-react';
import ProgressDashboard from '../components/ProgressDashboard';

const Progress: React.FC = () => {
  const [, setSelectedOperation] = useState<string | null>(null);

  const startOperation = async (operationType: string) => {
    try {
      const response = await fetch(`/api/progress/start/${operationType}`, { 
        method: 'POST' 
      });
      
      if (response.ok) {
        setSelectedOperation(operationType);
      } else {
        console.error('Failed to start operation');
      }
    } catch (error) {
      console.error('Error starting operation:', error);
    }
  };

  const operations = [
    {
      id: 'database_initialization',
      name: 'Database Initialization',
      description: 'Initialize database schema and load Canadian jurisdictions',
      icon: Database,
      color: 'bg-blue-600 hover:bg-blue-700',
    },
    {
      id: 'full_scrape',
      name: 'Full Data Scraping',
      description: 'Complete scraping of all Canadian jurisdictions',
      icon: Download,
      color: 'bg-green-600 hover:bg-green-700',
    },
    {
      id: 'federal_priority_scrape',
      name: 'Federal Priority Scraping',
      description: 'Enhanced federal bills and parliamentary data collection',
      icon: Settings,
      color: 'bg-purple-600 hover:bg-purple-700',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Progress Tracking</h1>
        <p className="mt-2 text-gray-600">
          Monitor and control data collection operations with real-time progress tracking
        </p>
      </div>

      {/* Quick Start Operations */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Start New Operation</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {operations.map((operation) => {
            const IconComponent = operation.icon;
            return (
              <button
                key={operation.id}
                onClick={() => startOperation(operation.id)}
                className={`p-4 rounded-lg text-white text-left transition-colors ${operation.color}`}
              >
                <div className="flex items-center mb-2">
                  <IconComponent className="w-6 h-6 mr-2" />
                  <h3 className="font-medium">{operation.name}</h3>
                </div>
                <p className="text-sm text-white/80">{operation.description}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Progress Dashboard */}
      <ProgressDashboard />

      {/* Help Information */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-900 mb-2">Progress Control Features</h3>
        <div className="text-blue-800 space-y-2">
          <p>• <strong>Pause/Resume:</strong> Temporarily halt operations and resume when ready</p>
          <p>• <strong>Skip Regions:</strong> Skip specific provinces or municipalities to continue with others</p>
          <p>• <strong>Skip Tasks:</strong> Skip individual tasks while continuing the overall operation</p>
          <p>• <strong>Real-time Updates:</strong> Live progress percentages and status updates</p>
          <p>• <strong>Error Handling:</strong> Detailed error messages and recovery options</p>
          <p>• <strong>ETA Calculation:</strong> Estimated completion times based on current progress</p>
        </div>
      </div>

      {/* Usage Instructions */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-2">How to Use</h3>
        <div className="text-gray-700 space-y-2">
          <p><strong>1. Start Operation:</strong> Click one of the operation buttons above to begin</p>
          <p><strong>2. Monitor Progress:</strong> Watch real-time updates in the progress dashboard</p>
          <p><strong>3. Control Execution:</strong> Use pause, skip, or cancel buttons as needed</p>
          <p><strong>4. Review Results:</strong> Check the tasks and regions tabs for detailed information</p>
        </div>
      </div>
    </div>
  );
};

export default Progress;