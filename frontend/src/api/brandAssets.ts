import axios from 'axios'
import { API_BASE_URL } from './client'

export interface BrandAsset {
  filename: string
  url: string
  size: number
  updated_at: number
}

export async function listBrandAssets(): Promise<BrandAsset[]> {
  const response = await axios.get(`${API_BASE_URL}/brand-assets`)
  return response.data.assets || []
}

export async function uploadBrandAsset(file: File, progress: (percent: number) => void): Promise<BrandAsset> {
  const formData = new FormData()
  formData.append('images', file)
  const response = await axios.post(`${API_BASE_URL}/brand-assets`, formData, {
    onUploadProgress(event) {
      if (event.total) progress(Math.round(event.loaded * 100 / event.total))
    }
  })
  const saved = response.data.assets?.[0]
  if (!saved?.filename || !saved.url) throw new Error('未收到收藏结果，请重新打开品牌素材库核对。')
  return saved
}

export async function brandAssetToFile(asset: BrandAsset): Promise<File> {
  const response = await fetch(asset.url)
  if (!response.ok) throw new Error('品牌素材加载失败')
  const blob = await response.blob()
  return new File([blob], asset.filename, { type: blob.type || 'image/png' })
}
