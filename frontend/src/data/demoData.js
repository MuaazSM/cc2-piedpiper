// Demo data — Mumbai/Pune/Delhi lanes matching synthetic_generator.py output

export const DEMO_SHIPMENTS = [
  { id: 'S001', origin: 'Mumbai',  destination: 'Pune',  weight: 4200, volume: 18, pickup_time: '2024-01-15T08:00', delivery_time: '2024-01-15T14:00', priority: 'high',   status: 'pending' },
  { id: 'S002', origin: 'Mumbai',  destination: 'Pune',  weight: 3100, volume: 12, pickup_time: '2024-01-15T09:00', delivery_time: '2024-01-15T15:00', priority: 'medium', status: 'pending' },
  { id: 'S003', origin: 'Mumbai',  destination: 'Delhi', weight: 5800, volume: 22, pickup_time: '2024-01-15T07:00', delivery_time: '2024-01-16T10:00', priority: 'high',   status: 'pending' },
  { id: 'S004', origin: 'Pune',    destination: 'Delhi', weight: 2900, volume: 10, pickup_time: '2024-01-15T10:00', delivery_time: '2024-01-16T12:00', priority: 'low',    status: 'pending' },
  { id: 'S005', origin: 'Mumbai',  destination: 'Pune',  weight: 1800, volume: 8,  pickup_time: '2024-01-15T08:30', delivery_time: '2024-01-15T13:30', priority: 'medium', status: 'pending' },
  { id: 'S006', origin: 'Delhi',   destination: 'Mumbai',weight: 6200, volume: 25, pickup_time: '2024-01-15T06:00', delivery_time: '2024-01-16T18:00', priority: 'high',   status: 'pending' },
]

export const DEMO_VEHICLES = [
  { id: 'V001', type: '20ft Container', capacity_weight: 10000, capacity_volume: 40, operating_cost: 4500, available: true },
  { id: 'V002', type: '20ft Container', capacity_weight: 10000, capacity_volume: 40, operating_cost: 4500, available: true },
  { id: 'V003', type: '40ft Container', capacity_weight: 18000, capacity_volume: 70, operating_cost: 7000, available: true },
  { id: 'V004', type: 'Mini Truck',     capacity_weight: 3000,  capacity_volume: 12, operating_cost: 2000, available: true },
]

export const DEMO_PLAN = {
  id: 'PLAN-001',
  created_at: '2024-01-15T10:30:00',
  trucks: [
    {
      vehicle_id: 'V001',
      vehicle_type: '20ft Container',
      shipments: ['S001', 'S002', 'S005'],
      total_weight: 9100,
      capacity_weight: 10000,
      utilization: 91,
      route: 'Mumbai → Pune',
      cost: 4500,
    },
    {
      vehicle_id: 'V003',
      vehicle_type: '40ft Container',
      shipments: ['S003'],
      total_weight: 5800,
      capacity_weight: 18000,
      utilization: 32,
      route: 'Mumbai → Delhi',
      cost: 7000,
    },
    {
      vehicle_id: 'V004',
      vehicle_type: 'Mini Truck',
      shipments: ['S004'],
      total_weight: 2900,
      capacity_weight: 3000,
      utilization: 97,
      route: 'Pune → Delhi',
      cost: 2000,
    },
  ],
}

export const DEMO_METRICS = {
  before: { trips: 6, avg_utilization: 62, total_cost: 24000, carbon_kg: 1440 },
  after:  { trips: 3, avg_utilization: 73, total_cost: 13500, carbon_kg: 810 },
  savings: {
    trips_reduced:    3,
    cost_saved:       10500,
    cost_saved_pct:   44,
    carbon_saved_kg:  630,
    carbon_saved_pct: 44,
  },
}

export const DEMO_SCENARIOS = [
  {
    id: 'strict_sla',
    label: 'Strict SLA',
    description: 'Hard delivery windows enforced',
    metrics: { trips: 4, avg_utilization: 68, total_cost: 15500, carbon_kg: 930 },
    feasible: true,
  },
  {
    id: 'flexible_sla',
    label: 'Flexible SLA',
    description: 'Windows relaxed ±30 min',
    metrics: { trips: 3, avg_utilization: 76, total_cost: 13500, carbon_kg: 810 },
    feasible: true,
  },
  {
    id: 'vehicle_shortage',
    label: 'Vehicle Shortage',
    description: 'Fleet reduced by 50%',
    metrics: { trips: 3, avg_utilization: 91, total_cost: 12000, carbon_kg: 720 },
    feasible: true,
  },
  {
    id: 'demand_surge',
    label: 'Demand Surge',
    description: '+40% shipment volume',
    metrics: { trips: 5, avg_utilization: 82, total_cost: 19000, carbon_kg: 1140 },
    feasible: true,
  },
]

export const DEMO_INSIGHTS = [
  {
    agent: 'Insight Agent',
    type: 'insight',
    message: 'Lane Mumbai–Pune consolidation feasible with 91% truck utilization. Grouping S001, S002, and S005 saves ₹10,500 vs. individual dispatch.',
  },
  {
    agent: 'Insight Agent',
    type: 'warning',
    message: 'Vehicle V003 (Mumbai→Delhi) is operating at only 32% utilization. Consider splitting S003 or waiting for an additional compatible shipment.',
  },
  {
    agent: 'Constraint Relaxation Agent',
    type: 'suggestion',
    message: 'Relaxing S003 delivery window by 45 minutes would allow consolidation with S006 (return Delhi→Mumbai), increasing utilization to 67%.',
  },
  {
    agent: 'Scenario Recommender',
    type: 'recommendation',
    message: 'For cost optimization: choose Flexible SLA (saves 44%). For carbon: choose Vehicle Shortage scenario (saves 50%). For SLA compliance: choose Strict SLA.',
  },
]

// City coordinates for Leaflet map
export const CITY_COORDS = {
  Mumbai: [19.0760, 72.8777],
  Pune:   [18.5204, 73.8567],
  Delhi:  [28.7041, 77.1025],
}