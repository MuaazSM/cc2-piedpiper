import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import useShipments from '@/hooks/useShipments'
import useOptimizer from '@/hooks/useOptimizer'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const shipmentsHook = useShipments()
  const optimizerHook = useOptimizer()

  // Shared optimization result (plan, insights, scenarios, metrics)
  const [optimizationResult, setOptimizationResult] = useState(null)

  // Load shipments on mount
  useEffect(() => {
    shipmentsHook.loadShipments()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const runFullOptimization = useCallback(async (params = {}) => {
    const data = await optimizerHook.runOptimization(params)
    if (data) {
      setOptimizationResult(data)
      // Reload shipments (status may have changed to ASSIGNED)
      shipmentsHook.loadShipments()
    }
    return data
  }, [optimizerHook, shipmentsHook])

  const value = {
    // Shipments
    shipments: shipmentsHook.shipments,
    shipmentsTotal: shipmentsHook.total,
    shipmentsLoading: shipmentsHook.loading,
    shipmentsError: shipmentsHook.error,
    loadShipments: shipmentsHook.loadShipments,
    createShipment: shipmentsHook.createShipment,
    seedData: shipmentsHook.seedData,

    // Optimization
    optimizerLoading: optimizerHook.loading,
    optimizerError: optimizerHook.error,
    optimizationResult,
    runFullOptimization,
    transformPlan: optimizerHook.transformPlan,
    runSimulation: optimizerHook.runSimulation,
    getMetrics: optimizerHook.getMetrics,
  }

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used within AppProvider')
  return ctx
}

export default AppContext
