import request from './request'

export function getDashboardOverview() {
  return request.get('/api/dashboard/overview')
}
