import { useState } from 'react'

export function useTab(initialTab) {
  const [activeTab, setActiveTab] = useState(initialTab)
  return { activeTab, setActiveTab }
}
