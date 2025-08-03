import type { VercelRequest, VercelResponse } from '@vercel/node'

export default function handler(req: VercelRequest, res: VercelResponse) {
  const { jurisdiction_id, jurisdiction_type, province, party, role, district, search, limit = 100, offset = 0 } = req.query

  // Mock data for demonstration
  const representatives = [
    {
      id: 'mp-001',
      name: 'Justin Trudeau',
      role: 'MP',
      party: 'Liberal',
      district: 'Papineau',
      email: 'justin.trudeau@parl.gc.ca',
      phone: '613-992-4211',
      jurisdiction_id: 'federal-parliament',
      jurisdiction: {
        id: 'federal-parliament',
        name: 'Parliament of Canada',
        jurisdiction_type: 'federal'
      },
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z'
    },
    {
      id: 'mpp-001',
      name: 'Doug Ford',
      role: 'MPP',
      party: 'Progressive Conservative',
      district: 'Etobicoke North',
      email: 'doug.ford@ola.org',
      phone: '416-325-7750',
      jurisdiction_id: 'ontario-legislature',
      jurisdiction: {
        id: 'ontario-legislature',
        name: 'Legislative Assembly of Ontario',
        jurisdiction_type: 'provincial',
        province: 'ON'
      },
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z'
    },
    {
      id: 'mayor-001',
      name: 'Olivia Chow',
      role: 'Mayor',
      party: 'Independent',
      district: 'Toronto',
      email: 'mayor@toronto.ca',
      phone: '416-397-3674',
      jurisdiction_id: 'toronto-city',
      jurisdiction: {
        id: 'toronto-city',
        name: 'City of Toronto',
        jurisdiction_type: 'municipal',
        province: 'ON'
      },
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z'
    }
  ]

  // Filter based on query parameters
  let filtered = representatives

  if (jurisdiction_id) {
    filtered = filtered.filter(r => r.jurisdiction_id === jurisdiction_id)
  }

  if (jurisdiction_type) {
    filtered = filtered.filter(r => r.jurisdiction?.jurisdiction_type === jurisdiction_type)
  }

  if (province) {
    filtered = filtered.filter(r => r.jurisdiction?.province === province)
  }

  if (party) {
    filtered = filtered.filter(r => r.party === party)
  }

  if (role) {
    filtered = filtered.filter(r => r.role === role)
  }

  if (district) {
    filtered = filtered.filter(r => r.district === district)
  }

  if (search) {
    filtered = filtered.filter(r => 
      r.name.toLowerCase().includes(search.toString().toLowerCase()) ||
      r.party?.toLowerCase().includes(search.toString().toLowerCase())
    )
  }

  // Apply pagination
  const paginated = filtered.slice(Number(offset), Number(offset) + Number(limit))

  res.status(200).json(paginated)
} 