export type ContentStyleId = 'general' | 'glumoo' | 'pet_education' | 'pet_product' | 'pet_lifestyle'

export const contentStyles: Array<{
  id: ContentStyleId
  name: string
  description: string
  badge?: string
}> = [
  { id: 'general', name: '智能通用', description: '根据主题自动选择表达方式' },
  { id: 'glumoo', name: 'Glumoo 专属', description: 'Pinterest 人宠生活摄影 · 固定 7 图', badge: '专属 SOP' },
  { id: 'pet_education', name: '宠物科普', description: '误区、原理、观察信号与安全建议' },
  { id: 'pet_product', name: '产品种草', description: '从真实痛点到使用体验，克制转化' },
  { id: 'pet_lifestyle', name: '养宠日常', description: '有时间、场景和宠物小动作的故事' }
]
