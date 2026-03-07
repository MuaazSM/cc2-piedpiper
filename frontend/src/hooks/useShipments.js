import { useState, useCallback } from 'react'
import { shipmentApi } from '@/services/api'

export default function useShipments() {
  const [shipments, setShipments] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const loadShipments = useCallback(async (params = {}) => {
    setLoading(true)
    setError(null)
    try {
      const data = await shipmentApi.getAll(params)
      setShipments(data.shipments ?? [])
      setTotal(data.total ?? 0)
      return data
    } catch (err) {
      setError(err.message)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const createShipment = useCallback(async (payload) => {
    setError(null)
    try {
      const created = await shipmentApi.create(payload)
      // Reload list after creation
      await loadShipments()
      return created
    } catch (err) {
      setError(err.message)
      return null
    }
  }, [loadShipments])

  const seedData = useCallback(async (params = {}) => {
    setLoading(true)
    setError(null)
    try {
      const result = await shipmentApi.seed(params)
      // Reload list after seeding
      await loadShipments()
      return result
    } catch (err) {
      setError(err.message)
      return null
    } finally {
      setLoading(false)
    }
  }, [loadShipments])

  return { shipments, total, loading, error, loadShipments, createShipment, seedData }
}
