import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
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

// Parliamentary types
export interface ParliamentarySession {
  id: number
  parliament_number: number
  session_number: number
  start_date: string
  end_date?: string
  hansard_records_count: number
  committee_meetings_count: number
}

export interface HansardRecord {
  id: number
  date: string
  sitting_number?: number
  document_url?: string
  pdf_url?: string
  xml_url?: string
  processed: boolean
  speech_count: number
}

export interface Speech {
  id: number
  hansard_id: number
  speaker_name?: string
  speaker_title?: string
  content: string
  time?: string
  subject?: string
  sequence_number: number
}

export interface ValidationResult {
  bill_id: string
  identifier: string
  title: string
  quality_score: number
  is_critical: boolean
  issues: string[]
  recommendations: string[]
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

// Scheduling API
export const schedulingApi = {
  scheduleTask: (taskType: 'test' | 'federal' | 'provincial' | 'municipal'): Promise<{ task_id: string }> =>
    api.post('/schedule', { task_type: taskType }).then(res => res.data),
  
  getTaskStatus: (taskId: string): Promise<TaskStatus> =>
    api.get(`/tasks/${taskId}`).then(res => res.data),
  
  cancelTask: (taskId: string): Promise<{ success: boolean }> =>
    api.delete(`/tasks/${taskId}`).then(res => res.data),
  
  getRecentRuns: (): Promise<ScrapingRun[]> =>
    api.get('/scraping-runs').then(res => res.data),
}

// Parliamentary API
export const parliamentaryApi = {
  getSessions: (): Promise<ParliamentarySession[]> =>
    api.get('/parliamentary/sessions').then(res => res.data),
  
  getHansardRecords: (params?: {
    session_id?: number
    start_date?: string
    end_date?: string
    processed?: boolean
    limit?: number
    offset?: number
  }): Promise<HansardRecord[]> => 
    api.get('/parliamentary/hansard', { params }).then(res => res.data),
  
  getSpeeches: (hansardId: number): Promise<Speech[]> =>
    api.get(`/parliamentary/hansard/${hansardId}/speeches`).then(res => res.data),
  
  searchSpeeches: (params: {
    query: string
    speaker?: string
    start_date?: string
    end_date?: string
    limit?: number
  }): Promise<Speech[]> =>
    api.get('/parliamentary/search/speeches', { params }).then(res => res.data),
  
  validateFederalBills: (): Promise<ValidationResult[]> =>
    api.get('/parliamentary/validation/federal-bills').then(res => res.data),
  
  getPolicyHealth: (): Promise<{ status: string; opa_version?: string }> =>
    api.get('/parliamentary/policy/health').then(res => res.data),
}

// Health check
export const healthApi = {
  getHealth: (): Promise<{ status: string; service: string }> =>
    api.get('/health').then(res => res.data),
}

export default api