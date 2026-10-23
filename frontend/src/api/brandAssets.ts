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

export async function uploadBrandAssets(files: File[]): Promise<BrandAsset[]> {
  const formData = new FormData()
  files.forEach(file => formData.append('images', file))
  const response = await axios.post(`${API_BASE_URL}/brand-assets`, formData)
  return response.data.assets || []
}

export async function brandAssetToFile(asset: BrandAsset): Promise<File> {
  const response = await fetch(asset.url)
  if (!response.ok) throw new Error('品牌素材加载失败')
  const blob = await response.blob()
  return new File([blob], asset.filename, { type: blob.type || 'image/png' })
}
