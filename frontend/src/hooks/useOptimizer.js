import { useState, useCallback } from 'react'
import { optimizeApi, simulateApi, metricsApi } from '@/services/api'

export default function useOptimizer() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const runOptimization = useCallback(async (params = {}) => {
    setLoading(true)
    setError(null)
    try {
      const data = await optimizeApi.run(params)
      setResult(data)
      return data
    } catch (err) {
      setError(err.message)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const runSimulation = useCallback(async (params = {}) => {
    setError(null)
    try {
      return await simulateApi.run(params)
    } catch (err) {
      setError(err.message)
      return null
    }
  }, [])

  const getMetrics = useCallback(async (planId) => {
    setError(null)
    try {
      return await metricsApi.get(planId)
    } catch (err) {
      setError(err.message)
      return null
    }
  }, [])

  const getPlan = useCallback(async (planId) => {
    setError(null)
    try {
      return await optimizeApi.getPlan(planId)
    } catch (err) {
      setError(err.message)
      return null
    }
  }, [])

  // Transform backend plan.assigned[] → frontend plan.trucks[] shape
  const transformPlan = useCallback((backendResult) => {
    if (!backendResult?.plan) return null
    const p = backendResult.plan
    return {
      id: p.id ?? 'PLAN-LIVE',
      created_at: p.created_at,
      status: p.status,
      total_trucks: p.total_trucks,
      trips_baseline: p.trips_baseline,
      avg_utilization: p.avg_utilization,
      cost_saving_pct: p.cost_saving_pct,
      carbon_saving_pct: p.carbon_saving_pct,
      trucks: (p.assigned || []).map(a => ({
        vehicle_id: a.vehicle_id,
        vehicle_type: a.vehicle_type ?? a.vehicle_id,
        shipments: a.shipment_ids ?? [],
        total_weight: a.total_weight ?? 0,
        capacity_weight: a.capacity_weight ?? 0,
        utilization: a.utilization_pct ?? 0,
        route: a.route ?? '',
        cost: a.cost ?? 0,
      })),
    }
  }, [])

  return {
    loading, error, result,
    runOptimization, runSimulation, getMetrics, getPlan, transformPlan,
  }
}
