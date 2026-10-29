export type ContentStyleId =
  | 'general' | 'glumoo'
  | 'glumoo_1' | 'glumoo_2' | 'glumoo_3' | 'glumoo_4' | 'glumoo_5' | 'glumoo_6'
  | 'glumoo_7' | 'glumoo_8' | 'glumoo_9' | 'glumoo_10' | 'glumoo_11'
  | 'glumoo_12' | 'glumoo_13' | 'glumoo_14' | 'glumoo_15'
  | 'pet_education' | 'pet_product' | 'pet_lifestyle'

export const contentStyles: Array<{
  id: ContentStyleId
  name: string
  description: string
  badge?: string
}> = [
  { id: 'general', name: '智能通用', description: '根据主题自动选择表达方式' },
  { id: 'glumoo', name: 'Glumoo 自由创意', description: '六图动态归纳，不预设场景类型', badge: '完整 SOP' },
  { id: 'glumoo_1', name: '风格 1 · 趣味波普社媒', description: '高饱和、趣味造型、真实社媒摄影' },
  { id: 'glumoo_2', name: '风格 2 · 日光家庭纪实', description: '自然日光与真实家庭生活瞬间' },
  { id: 'glumoo_3', name: '风格 3 · 高饱和几何色块', description: '几何空间与明确冷暖色块' },
  { id: 'glumoo_4', name: '风格 4 · 品牌蓝雕塑静物', description: '品牌蓝、雕塑层次、精准静物' },
  { id: 'glumoo_5', name: '风格 5 · 户外机能远征', description: '真实地貌、机能装备与行动感' },
  { id: 'glumoo_6', name: '风格 6 · 成分证据编辑', description: '可核实成分、用法与边界叙事' },
  { id: 'glumoo_7', name: '风格 7 · 瑞士海报编辑', description: '网格、留白与克制编辑秩序' },
  { id: 'glumoo_8', name: '风格 8 · 35mm 时装纪实', description: '现场感、自然颗粒与时装构图' },
  { id: 'glumoo_9', name: '风格 9 · 超现实冷幽默', description: '单一反差概念，物理关系仍真实' },
  { id: 'glumoo_10', name: '风格 10 · 触感微距感官', description: '毛发、手、材质与产品触感' },
  { id: 'glumoo_11', name: '风格 11 · 策展式编辑拼贴', description: '策展并置与材料层次' },
  { id: 'glumoo_12', name: '风格 12 · 超广角亲密视角', description: '近距离透视与亲密镜头互动' },
  { id: 'glumoo_13', name: '风格 13 · 俯拍生活图谱', description: '真实同平面生活物件关系' },
  { id: 'glumoo_14', name: '风格 14 · 高速瞬间定格', description: '清晰冻结动作与视线因果' },
  { id: 'glumoo_15', name: '风格 15 · 节日生活方式', description: '按主题变化的克制节日叙事' },
  { id: 'pet_education', name: '宠物科普', description: '误区、原理、观察信号与安全建议' },
  { id: 'pet_product', name: '产品种草', description: '从真实痛点到使用体验，克制转化' },
  { id: 'pet_lifestyle', name: '养宠日常', description: '有时间、场景和宠物小动作的故事' }
]
