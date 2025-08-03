import type { VercelRequest, VercelResponse } from '@vercel/node'

export default function handler(req: VercelRequest, res: VercelResponse) {
  const { jurisdiction_type, province, limit = 100, offset = 0 } = req.query

  // Mock data for demonstration
  const jurisdictions = [
    {
      id: 'federal-parliament',
      name: 'Parliament of Canada',
      jurisdiction_type: 'federal',
      url: 'https://www.parl.ca',
      api_url: 'https://api.parliament.ca',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z'
    },
    {
      id: 'ontario-legislature',
      name: 'Legislative Assembly of Ontario',
      jurisdiction_type: 'provincial',
      province: 'ON',
      url: 'https://www.ola.org',
      api_url: 'https://api.ola.org',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z'
    },
    {
      id: 'toronto-city',
      name: 'City of Toronto',
      jurisdiction_type: 'municipal',
      province: 'ON',
      url: 'https://www.toronto.ca',
      api_url: 'https://api.toronto.ca',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z'
    }
  ]

  // Filter based on query parameters
  let filtered = jurisdictions

  if (jurisdiction_type) {
    filtered = filtered.filter(j => j.jurisdiction_type === jurisdiction_type)
  }

  if (province) {
    filtered = filtered.filter(j => j.province === province)
  }

  // Apply pagination
  const paginated = filtered.slice(Number(offset), Number(offset) + Number(limit))

  res.status(200).json(paginated)
} 