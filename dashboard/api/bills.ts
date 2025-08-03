import type { VercelRequest, VercelResponse } from '@vercel/node'

export default function handler(req: VercelRequest, res: VercelResponse) {
  const { jurisdiction_id, status, search, limit = 100, offset = 0 } = req.query

  // Mock data for demonstration
  const bills = [
    {
      id: 'bill-001',
      identifier: 'C-123',
      title: 'An Act to amend the Criminal Code (assault weapons)',
      summary: 'This bill proposes amendments to the Criminal Code to strengthen regulations on assault weapons.',
      status: 'first_reading',
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
      id: 'bill-002',
      identifier: 'S-456',
      title: 'An Act respecting the establishment of a national pharmacare program',
      summary: 'This bill establishes a framework for a national pharmacare program to provide prescription drug coverage.',
      status: 'second_reading',
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
      id: 'bill-003',
      identifier: 'Bill 123',
      title: 'Ontario Health and Safety Act, 2025',
      summary: 'An Act to improve workplace health and safety standards in Ontario.',
      status: 'passed',
      jurisdiction_id: 'ontario-legislature',
      jurisdiction: {
        id: 'ontario-legislature',
        name: 'Legislative Assembly of Ontario',
        jurisdiction_type: 'provincial',
        province: 'ON'
      },
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z'
    }
  ]

  // Filter based on query parameters
  let filtered = bills

  if (jurisdiction_id) {
    filtered = filtered.filter(b => b.jurisdiction_id === jurisdiction_id)
  }

  if (status) {
    filtered = filtered.filter(b => b.status === status)
  }

  if (search) {
    filtered = filtered.filter(b => 
      b.title.toLowerCase().includes(search.toString().toLowerCase()) ||
      b.summary?.toLowerCase().includes(search.toString().toLowerCase()) ||
      b.identifier.toLowerCase().includes(search.toString().toLowerCase())
    )
  }

  // Apply pagination
  const paginated = filtered.slice(Number(offset), Number(offset) + Number(limit))

  res.status(200).json(paginated)
} 