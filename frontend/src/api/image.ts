import axios from 'axios'
import {
  API_BASE_URL,
  readErrorResponse,
  readSseResponse
} from './client'
import type {
  FinishEvent,
  Page,
  ProgressEvent
} from './types'
import type { AppError } from '../utils/errors'
import type { ContentStyleId } from '../contentStyles'

export function getImageUrl(taskId: string, filename: string, thumbnail: boolean = true): string {
  const thumbParam = thumbnail ? '?thumbnail=true' : '?thumbnail=false'
  return `${API_BASE_URL}/images/${taskId}/${filename}${thumbParam}`
}

export async function regenerateImage(
  taskId: string,
  page: Page,
  useReference: boolean = true,
  context?: {
    fullOutline?: string
    userTopic?: string
    recordId?: string | null
  }
): Promise<{ success: boolean; index: number; image_url?: string; error?: AppError | string; error_message?: string }> {
  const response = await axios.post(`${API_BASE_URL}/regenerate`, {
    task_id: taskId,
    page,
    use_reference: useReference,
    full_outline: context?.fullOutline,
    user_topic: context?.userTopic,
    record_id: context?.recordId || undefined
  })
  return response.data
}

export async function retryFailedImages(
  taskId: string,
  pages: Page[],
  onProgress: (event: ProgressEvent) => void,
  onComplete: (event: ProgressEvent) => void,
  onError: (event: ProgressEvent) => void,
  onFinish: (event: { success: boolean; total: number; completed: number; failed: number }) => void,
  onStreamError: (error: unknown) => void,
  recordId?: string | null
) {
  try {
    const response = await fetch(`${API_BASE_URL}/retry-failed`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        task_id: taskId,
        pages,
        record_id: recordId || undefined
      })
    })

    if (!response.ok) {
      throw await readErrorResponse(response, `请求失败：HTTP ${response.status}`)
    }

    await readSseResponse(response, {
      retry_start: (data) => onProgress({ index: -1, status: 'generating', message: data.message }),
      complete: onComplete,
      error: onError,
      retry_finish: onFinish
    })
  } catch (error) {
    onStreamError(error)
  }
}

export async function generateImagesPost(
  pages: Page[],
  taskId: string | null,
  fullOutline: string,
  onProgress: (event: ProgressEvent) => void,
  onComplete: (event: ProgressEvent) => void,
  onError: (event: ProgressEvent) => void,
  onFinish: (event: FinishEvent) => void,
  onStreamError: (error: unknown) => void,
  userImages?: File[],
  userTopic?: string,
  recordId?: string | null,
  force: boolean = false,
  layoutMimicMode: boolean = false,
  platform: 'xiaohongshu' | 'instagram' = 'xiaohongshu',
  styleId: ContentStyleId = 'general',
  productImages?: File[]
) {
  try {
    const userImagesBase64 = userImages && userImages.length > 0
      ? await Promise.all(userImages.map(readFileAsDataUrl))
      : []
    const productImagesBase64 = productImages && productImages.length > 0
      ? await Promise.all(productImages.map(readFileAsDataUrl))
      : []

    const response = await fetch(`${API_BASE_URL}/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        pages,
        task_id: taskId,
        full_outline: fullOutline,
        user_images: userImagesBase64.length > 0 ? userImagesBase64 : undefined,
        product_images: productImagesBase64.length > 0 ? productImagesBase64 : undefined,
        user_topic: userTopic || '',
        record_id: recordId || undefined,
        force,
        layout_mimic_mode: layoutMimicMode,
        platform,
        style_id: styleId
      })
    })

    if (!response.ok) {
      throw await readErrorResponse(response, `请求失败：HTTP ${response.status}`)
    }

    await readSseResponse(response, {
      progress: onProgress,
      complete: onComplete,
      error: onError,
      finish: onFinish
    })
  } catch (error) {
    onStreamError(error)
  }
}

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}
