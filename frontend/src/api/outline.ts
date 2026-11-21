import axios from 'axios'
import { API_BASE_URL } from './client'
import type { OutlineResponse } from './types'
import type { ContentStyleId } from '../contentStyles'

import type { NoteReference } from './studio'

export async function generateOutline(
  topic: string,
  images?: File[],
  platform: 'xiaohongshu' | 'instagram' = 'xiaohongshu',
  styleId: ContentStyleId = 'general',
  productImages?: File[],
  researchId?: string,
  noteReferences: NoteReference[] = []
): Promise<OutlineResponse & { has_images?: boolean }> {
  if ((images && images.length > 0) || (productImages && productImages.length > 0)) {
    const formData = new FormData()
    formData.append('topic', topic)
    formData.append('platform', platform)
    if (noteReferences.length) formData.append('note_references', JSON.stringify(noteReferences))
    if (researchId) formData.append('research_id', researchId)
    formData.append('style_id', styleId)
    ;(images || []).forEach((file) => {
      formData.append('images', file)
    })
    ;(productImages || []).forEach((file) => formData.append('product_images', file))

    const response = await axios.post<OutlineResponse & { has_images?: boolean }>(
      `${API_BASE_URL}/outline`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    return response.data
  }

  const response = await axios.post<OutlineResponse>(`${API_BASE_URL}/outline`, {
    topic,
    platform,
    research_id: researchId,
    note_references: noteReferences,
    style_id: styleId
  })
  return response.data
}
