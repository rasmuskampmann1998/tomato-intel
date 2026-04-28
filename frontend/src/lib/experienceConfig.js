export const EXPERIENCE_CONFIG = {
  researcher: {
    label: 'Researcher',
    icon: '🔍',
    color: 'blue',
    description: 'Market analyst · news, patents, regulations, competitors',
    defaultCategorySlugs: ['news', 'competitors', 'patents', 'regulations', 'social', 'crops', 'genetics'],
    cardStyle: 'article',
  },
  grower: {
    label: 'Grower',
    icon: '🌱',
    color: 'green',
    description: 'Farmer · crop alerts, disease, growing advice',
    defaultCategorySlugs: ['crops', 'news', 'regulations', 'social', 'competitors', 'patents', 'genetics'],
    cardStyle: 'alert',
  },
  breeder: {
    label: 'Breeder',
    icon: '🧬',
    color: 'purple',
    description: 'Plant scientist · genetics, patents, variety launches',
    defaultCategorySlugs: ['genetics', 'patents', 'competitors', 'news', 'regulations', 'crops', 'social'],
    cardStyle: 'data',
  },
}

export function getCategoryOrder(experience, categories) {
  const config = EXPERIENCE_CONFIG[experience] || EXPERIENCE_CONFIG.researcher
  const order = config.defaultCategorySlugs
  return [...categories].sort((a, b) => {
    const ai = order.indexOf(a.slug)
    const bi = order.indexOf(b.slug)
    if (ai === -1 && bi === -1) return 0
    if (ai === -1) return 1
    if (bi === -1) return -1
    return ai - bi
  })
}
