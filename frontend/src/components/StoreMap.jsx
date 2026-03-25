import { useEffect } from 'react'
import L from 'leaflet'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './StoreMap.css'

/** Vite 번들에서 기본 마커 아이콘이 깨지지 않도록 설정 */
function useFixLeafletIcons() {
  useEffect(() => {
    delete L.Icon.Default.prototype._getIconUrl
    L.Icon.Default.mergeOptions({
      iconRetinaUrl:
        'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
      iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    })
  }, [])
}

/**
 * OpenStreetMap 타일을 사용하는 근처 매장 위치 맵입니다.
 * @param {{ lat: number; lng: number }} center
 */
function StoreMap({ center }) {
  useFixLeafletIcons()

  return (
    <div className="store-map-wrap">
      <MapContainer
        center={[center.lat, center.lng]}
        zoom={14}
        className="store-map"
        scrollWheelZoom
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={[center.lat, center.lng]}>
          <Popup>구매 가능 매장 (예시 위치)</Popup>
        </Marker>
      </MapContainer>
    </div>
  )
}

export default StoreMap
