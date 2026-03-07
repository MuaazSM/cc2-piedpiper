import { MapContainer, TileLayer, Marker, Polyline, Popup, CircleMarker } from 'react-leaflet'
import L from 'leaflet'
import { CITY_COORDS } from '@/data/demoData'

// Fix Leaflet default icon
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl:       'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl:     'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

const GROUP_COLORS = ['#f59e0b', '#06b6d4', '#10b981', '#8b5cf6', '#f43f5e', '#fb923c']

export default function ShipmentMap({ shipments = [], selectedId = null }) {
  return (
    <MapContainer
      center={[20.5, 76]}
      zoom={6}
      style={{ height: '100%', width: '100%' }}
      zoomControl={false}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="© OpenStreetMap"
      />

      {/* City markers */}
      {Object.entries(CITY_COORDS).map(([city, coords]) => (
        <CircleMarker key={city} center={coords} radius={8}
          pathOptions={{ color: '#f5f5f5', fillColor: '#1a1a1a', fillOpacity: 1, weight: 2 }}>
          <Popup>{city}</Popup>
        </CircleMarker>
      ))}

      {/* Route lines */}
      {shipments.map((s, i) => {
        const from = CITY_COORDS[s.origin]
        const to   = CITY_COORDS[s.destination]
        if (!from || !to) return null
        const color = GROUP_COLORS[i % GROUP_COLORS.length]
        const isSelected = s.id === selectedId
        return (
          <Polyline key={s.id}
            positions={[from, to]}
            pathOptions={{
              color,
              weight:  isSelected ? 4 : 2,
              opacity: isSelected ? 1 : 0.6,
              dashArray: '6 4',
            }}>
            <Popup>
              <span style={{ fontFamily: 'DM Sans', fontSize: 12 }}>
                {s.id}: {s.origin} → {s.destination}<br/>
                {s.weight.toLocaleString()} kg
              </span>
            </Popup>
          </Polyline>
        )
      })}
    </MapContainer>
  )
}