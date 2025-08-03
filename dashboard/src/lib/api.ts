import axios from 'axios'

const api = axios.create({
  baseURL: 'http://192.168.2.152:8000',
  timeout: 30000,
})

// Types
export interface Stats {
  total_jurisdictions: number
  federal_jurisdictions: number
  provincial_jurisdictions: number
  municipal_jurisdictions: number
  total_representatives: number
  total_bills: number
  total_committees: number
  total_events: number
  total_votes: number
  representatives_mp?: number
  representatives_mpp?: number
  representatives_mla?: number
  representatives_mayor?: number
  representatives_councillor?: number
}

export interface Jurisdiction {
  id: string
  name: string
  jurisdiction_type: 'federal' | 'provincial' | 'municipal'
  province?: string
  url?: string
  api_url?: string
  created_at: string
  updated_at: string
}

export interface Representative {
  id: string
  name: string
  role: string
  party?: string
  district?: string
  email?: string
  phone?: string
  jurisdiction_id: string
  jurisdiction?: Jurisdiction
  created_at: string
  updated_at: string
}

export interface Bill {
  id: string
  identifier: string
  title: string
  summary?: string
  status: string
  jurisdiction_id: string
  jurisdiction?: Jurisdiction
  created_at: string
  updated_at: string
}

export interface ScrapingRun {
  id: string
  task_id: string
  jurisdiction_types: string[]
  status: 'pending' | 'running' | 'completed' | 'failed'
  records_created: number
  records_updated: number
  errors_count: number
  started_at?: string
  completed_at?: string
  error_message?: string
}

export interface TaskStatus {
  task_id: string
  status: string
  result?: any
  error?: string
  traceback?: string
}

// API functions
export const statsApi = {
  getStats: (): Promise<Stats> => api.get('/stats').then(res => res.data),
}

export const jurisdictionsApi = {
  getJurisdictions: (params?: {
    jurisdiction_type?: string
    province?: string
    limit?: number
    offset?: number
  }): Promise<Jurisdiction[]> => api.get('/jurisdictions', { params }).then(res => res.data),
  
  getJurisdiction: (id: string): Promise<Jurisdiction> => 
    api.get(`/jurisdictions/${id}`).then(res => res.data),
}

export const representativesApi = {
  getRepresentatives: (params?: {
    jurisdiction_id?: string
    jurisdiction_type?: string
    province?: string
    party?: string
    role?: string
    district?: string
    search?: string
    limit?: number
    offset?: number
  }): Promise<Representative[]> => api.get('/representatives', { params }).then(res => res.data),
  
  getRepresentative: (id: string): Promise<Representative> => 
    api.get(`/representatives/${id}`).then(res => res.data),
}

export const billsApi = {
  getBills: (params?: {
    jurisdiction_id?: string
    status?: string
    search?: string
    limit?: number
    offset?: number
  }): Promise<Bill[]> => api.get('/bills', { params }).then(res => res.data),
  
  getBill: (id: string): Promise<Bill> => 
    api.get(`/bills/${id}`).then(res => res.data),
}

export const schedulingApi = {
  scheduleTask: (taskType: 'test' | 'federal' | 'provincial' | 'municipal'): Promise<TaskStatus> =>
    api.post('/scheduling/schedule', { task_type: taskType }).then(res => res.data),
  
  cancelTask: (taskId: string): Promise<void> =>
    api.post(`/scheduling/cancel/${taskId}`).then(res => res.data),
  
  getRecentRuns: (): Promise<ScrapingRun[]> =>
    api.get('/scheduling/recent-runs').then(res => res.data),
}

export const healthApi = {
  getHealth: (): Promise<{ status: string; service: string }> =>
    api.get('/health').then(res => res.data),
}

export default api