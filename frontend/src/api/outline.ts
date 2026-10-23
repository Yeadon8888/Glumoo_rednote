import axios from 'axios'
import { API_BASE_URL } from './client'
import type { OutlineResponse } from './types'
import type { ContentStyleId } from '../contentStyles'

export async function generateOutline(
  topic: string,
  images?: File[],
  platform: 'xiaohongshu' | 'instagram' = 'xiaohongshu',
  styleId: ContentStyleId = 'general'
): Promise<OutlineResponse & { has_images?: boolean }> {
  if (images && images.length > 0) {
    const formData = new FormData()
    formData.append('topic', topic)
    formData.append('platform', platform)
    formData.append('style_id', styleId)
    images.forEach((file) => {
      formData.append('images', file)
    })

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
    style_id: styleId
  })
  return response.data
}
