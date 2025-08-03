import type { VercelRequest, VercelResponse } from '@vercel/node'

export default function handler(_req: VercelRequest, res: VercelResponse) {
  // Mock data for demonstration
  const stats = {
    total_jurisdictions: 123,
    federal_jurisdictions: 1,
    provincial_jurisdictions: 14,
    municipal_jurisdictions: 108,
    total_representatives: 2847,
    total_bills: 156,
    total_committees: 89,
    total_events: 342,
    total_votes: 1256,
    representatives_mp: 338,
    representatives_mpp: 425,
    representatives_mla: 0,
    representatives_mayor: 108,
    representatives_councillor: 1976
  }

  res.status(200).json(stats)
} 