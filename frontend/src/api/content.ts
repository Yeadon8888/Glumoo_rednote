import axios from 'axios'
import { API_BASE_URL } from './client'
import type { ContentResponse } from './types'
import type { ContentStyleId } from '../contentStyles'

export async function generateContent(
  topic: string,
  outline: string,
  platform: 'xiaohongshu' | 'instagram' = 'xiaohongshu',
  styleId: ContentStyleId = 'general'
): Promise<ContentResponse> {
  const response = await axios.post<ContentResponse>(`${API_BASE_URL}/content`, {
    topic,
    outline,
    platform,
    style_id: styleId
  })
  return response.data
}
