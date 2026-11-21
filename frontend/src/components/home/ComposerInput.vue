<template>
  <!-- 主题输入组合框 -->
  <div class="composer-container">
    <!-- 输入区域 -->
    <div class="composer-input-wrapper">
      <div class="search-icon-static">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M21 21L16.65 16.65M19 11C19 15.4183 15.4183 19 11 19C6.58172 19 3 15.4183 3 11C3 6.58172 6.58172 3 11 3C15.4183 3 19 6.58172 19 11Z" stroke="#999" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <textarea
        ref="textareaRef"
        :value="modelValue"
        @input="handleInput"
        class="composer-textarea"
        placeholder="输入主题，例如：金毛夏日消暑攻略..."
        :disabled="loading"
        rows="1"
      ></textarea>
    </div>

    <NoteReferences ref="notePanel" :disabled="loading" />
    <div class="style-section">
      <div class="style-heading">
        <h2 id="reference-style-heading">参考风格</h2>
        <button type="button" class="asset-button" :aria-pressed="favorites.includes(chosenStyle)" @click="toggleFavorite">
          {{ favorites.includes(chosenStyle) ? '移出常用' : '设为常用' }}
        </button>
      </div>
      <div class="style-grid" role="radiogroup" aria-labelledby="reference-style-heading">
        <label v-for="style in sortedStyles" :key="style.id" class="style-card"
          :class="{ selected: style.id === chosenStyle }">
          <input v-model="chosenStyle" type="radio" name="reference-style" :value="style.id"
            :aria-label="style.name" :disabled="loading">
          <span class="style-name">{{ style.name }}</span>
          <span class="style-copy">{{ style.description }}</span>
          <span v-if="style.badge || favorites.includes(style.id)" class="style-meta">
            {{ [style.badge, favorites.includes(style.id) ? '常用' : ''].filter(Boolean).join(' · ') }}
          </span>
        </label>
      </div>
      <ResearchPanel ref="researchPanel" :topic="modelValue" :style-id="chosenStyle" :disabled="loading"
        :upload-count="uploadedImages.length" />
    </div>
    <!-- 已上传图片预览 -->
    <div v-if="uploadedImages.length > 0" class="uploaded-images-preview">
      <div
        v-for="(img, idx) in uploadedImages"
        :key="idx"
        class="uploaded-image-item"
      >
        <img :src="img.preview" :alt="`图片 ${idx + 1}`" />
        <button class="remove-image-btn" @click="removeImage(idx)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
      <div class="upload-hint">
        这些图片将用于生成封面和内容参考
      </div>
    </div>

    <div class="asset-library">
      <div class="asset-library-bar">
        <button type="button" class="asset-button" @click="toggleAssetLibrary" :disabled="loading || assetBusy">
          品牌素材库 <span v-if="brandAssets.length">{{ brandAssets.length }}</span>
        </button>
        <button type="button" class="asset-button" :disabled="loading || assetBusy" @click="assetInput?.click()">
          {{ uploading ? '正在收藏…' : '上传并收藏' }}
        </button>
        <input ref="assetInput" type="file" accept="image/png,image/jpeg,image/webp" multiple hidden @change="handleBrandAssetUpload" />
      </div>
      <p v-if="assetMessage" class="asset-status" role="status">{{ assetMessage }}</p>
      <p v-if="assetError" class="asset-error" role="alert">{{ assetError }}</p>
      <div v-if="showAssetLibrary" class="asset-grid">
        <button
          v-for="asset in brandAssets"
          :key="asset.filename"
          type="button"
          class="asset-card"
          :class="{ selected: selectedProductNames.has(asset.filename) }"
          :disabled="loading || assetBusy"
          :aria-pressed="selectedProductNames.has(asset.filename)"
          @click="useBrandAsset(asset)"
        >
          <img :src="asset.url + '?preview=1'" alt="品牌素材" loading="lazy" />
          <span>{{ selectedProductNames.has(asset.filename) ? '已引用' : recentAssets.includes(asset.filename) ? '刚收藏 · 点击引用' : '点击引用' }}</span>
        </button>
        <span v-if="brandAssets.length === 0 && !assetBusy && !assetError" class="empty-assets">还没有素材，可上传产品图、Logo 或品牌参考图。</span>
      </div>
      <div v-if="selectedProductImages.length" class="product-selection-summary">
        已选择 {{ selectedProductImages.length }} 张产品资产；它们与六张主参考分开传入。
        <button type="button" class="clear-product-assets" @click="clearProductAssets">清空产品资产</button>
      </div>
    </div>

    <!-- 一键二创选项 -->
    <div v-if="uploadedImages.length > 0" class="layout-mimic-option">
      <label class="checkbox-label">
        <input
          type="checkbox"
          v-model="layoutMimicMode"
          @change="handleLayoutMimicChange"
          :disabled="loading"
        />
        <span class="checkbox-custom"></span>
        <span class="checkbox-text">
          <span class="option-title">一键二创模式</span>
          <span class="option-desc">严格模仿参考图的布局结构，只替换文字内容（推荐用于小红书爆款图片）</span>
        </span>
      </label>
    </div>

    <!-- 工具栏 -->
    <div class="composer-toolbar">
      <div class="toolbar-left">
        <label class="tool-btn" :class="{ 'active': uploadedImages.length > 0 }" title="上传参考图">
          <input
            type="file"
            accept="image/*"
            multiple
            @change="handleImageUpload"
            :disabled="loading"
            style="display: none;"
          />
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <circle cx="8.5" cy="8.5" r="1.5"></circle>
            <polyline points="21 15 16 10 5 21"></polyline>
          </svg>
          <span v-if="uploadedImages.length > 0" class="badge-count">{{ uploadedImages.length }}</span>
        </label>

        <!-- 平台选择下拉框 -->
        <select
          class="platform-select"
          v-model="selectedPlatform"
          @change="handlePlatformChange"
          :disabled="loading"
          title="选择内容平台风格"
        >
          <option value="xiaohongshu">小红书</option>
          <option value="instagram">Instagram</option>
        </select>
      </div>
      <div class="toolbar-right">
        <button
          class="btn btn-primary generate-btn"
          @click="$emit('generate')"
          :disabled="!modelValue.trim() || loading || !!preparationHint"
        >
          <span v-if="loading" class="spinner-sm"></span>
          <span>{{ loading ? '生成中' : '生成大纲' }}</span>
        </button>
      </div>
    </div>

    <p v-if="preparationHint && !loading" class="style-description" role="status">{{ preparationHint }}</p>
    <div v-if="loading" class="loading-hint" role="status" aria-live="polite">
      请稍后，这一步大概要 15-30 秒左右。
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onUnmounted } from 'vue'
import ResearchPanel from './ResearchPanel.vue'
import NoteReferences from './NoteReferences.vue'
const notePanel = ref<InstanceType<typeof NoteReferences>|null>(null)
const researchPanel=ref<InstanceType<typeof ResearchPanel>|null>(null)
const favorites=ref<string[]>([])
try {const saved=JSON.parse(localStorage.getItem('glumoo.favoriteStyles')||'[]');if(Array.isArray(saved))favorites.value=saved.filter(x=>typeof x==='string')} catch {}
const sortedStyles=computed(()=>[...contentStyles].sort((a,b)=>Number(favorites.value.includes(b.id))-Number(favorites.value.includes(a.id))))
function toggleFavorite(){const id=store.contentStyle;favorites.value=favorites.value.includes(id)?favorites.value.filter(x=>x!==id):[...favorites.value,id];localStorage.setItem('glumoo.favoriteStyles',JSON.stringify(favorites.value))}

import { normalizeApiError } from '../../utils/errors'
import { contentStyles } from '../../contentStyles'
import {
  brandAssetToFile,
  listBrandAssets,
  uploadBrandAsset,
  type BrandAsset
} from '../../api/brandAssets'

/**
 * 主题输入组合框组件
 *
 * 功能：
 * - 主题文本输入（自动调整高度）
 * - 参考图片上传（最多8张）
 * - 生成按钮
 */

// 定义上传的图片类型
interface UploadedImage {
  file: File
  preview: string
}

// 定义 Props
const props = defineProps<{
  modelValue: string
  loading: boolean
}>()

// 定义 Emits
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'generate'): void
  (e: 'imagesChange', images: File[]): void
  (e: 'productImagesChange', images: File[]): void
  (e: 'layoutMimicChange', enabled: boolean): void
  (e: 'platformChange', platform: string): void
}>()

// 输入框引用
const textareaRef = ref<HTMLTextAreaElement | null>(null)

// 已上传的图片
const uploadedImages = ref<UploadedImage[]>([])
const selectedProductImages = ref<Array<UploadedImage & { filename: string }>>([])
const selectedProductNames = ref(new Set<string>())
const brandAssets = ref<BrandAsset[]>([])
const showAssetLibrary = ref(false)
const assetInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const readingAssets = ref(false)
const assetBusy = computed(() => uploading.value || readingAssets.value)
const assetMessage = ref('')
const assetError = ref('')
const recentAssets = ref<string[]>([])

// 一键二创模式
const layoutMimicMode = ref(false)

// 平台选择（从 store 同步初始值，确保与实际发送的值一致）
import { useGeneratorStore } from '../../stores/generator'
const store = useGeneratorStore()
const chosenStyle = computed({get: () => store.contentStyle, set: value => store.setContentStyle(value)})
const preparationHint = computed(() => {
  if (assetBusy.value) return '正在处理品牌素材，请稍候。'
  if (notePanel.value?.pending) return '请先添加正在编辑的笔记，或清空输入框。'
  if (researchPanel.value?.working) return '请先完成当前的调研或选图。'
  if (chosenStyle.value.startsWith('glumoo') && uploadedImages.value.length !== 6 &&
      (uploadedImages.value.length > 0 || researchPanel.value?.picks.length !== 6))
    return '请先匹配、从库中选择，或上传六张参考图。'
  return ''
})
const selectedPlatform = ref(store.platform || 'xiaohongshu')

/**
 * 处理输入变化
 */
function handleInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)
  adjustHeight()
}

/**
 * 自动调整输入框高度
 */
function adjustHeight() {
  const el = textareaRef.value
  if (!el) return

  el.style.height = 'auto'
  const newHeight = Math.max(64, Math.min(el.scrollHeight, 200))
  el.style.height = newHeight + 'px'
}

/**
 * 处理图片上传
 */
function handleImageUpload(event: Event) {
  const target = event.target as HTMLInputElement
  if (!target.files) return

  const files = Array.from(target.files)
  files.forEach((file) => {
    // 限制最多 8 张图片
    if (uploadedImages.value.length >= 8) {
      return
    }
    // 创建预览 URL
    const preview = URL.createObjectURL(file)
    uploadedImages.value.push({ file, preview })
  })

  // 通知父组件
  emitImagesChange()

  // 清空 input，允许重复选择同一文件
  target.value = ''
}

/**
 * 移除图片
 */
function removeImage(index: number) {
  const img = uploadedImages.value[index]
  // 释放预览 URL
  URL.revokeObjectURL(img.preview)
  uploadedImages.value.splice(index, 1)

  // 通知父组件
  emitImagesChange()
}

/**
 * 通知父组件图片变化
 */
function emitImagesChange() {
  const files = uploadedImages.value.map(img => img.file)
  emit('imagesChange', files)
}

async function toggleAssetLibrary() {
  if (assetBusy.value) return
  showAssetLibrary.value = !showAssetLibrary.value
  if (!showAssetLibrary.value) return
  readingAssets.value = true
  assetError.value = ''
  try {
    brandAssets.value = await listBrandAssets()
  } catch (error) {
    assetError.value = '素材库读取失败：' + normalizeApiError(error).detail
  } finally {
    readingAssets.value = false
  }
}

async function handleBrandAssetUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files || [])
  target.value = ''
  if (!files.length || assetBusy.value) return
  uploading.value = true
  assetError.value = ''
  recentAssets.value = []
  let saved = 0
  try {
    for (const file of files) {
      const label = `第 ${saved + 1}/${files.length} 张 · ${file.name}`
      assetMessage.value = `正在上传 ${label}`
      const asset = await uploadBrandAsset(file, percent => {
        assetMessage.value = percent < 100 ? `正在上传 ${label} · ${percent}%` : `正在保存 ${label}`
      })
      brandAssets.value = [asset, ...brandAssets.value.filter(item => item.filename !== asset.filename)]
      recentAssets.value.push(asset.filename)
      showAssetLibrary.value = true
      saved++
    }
    assetMessage.value = `已收藏 ${saved} 张产品图，点击图片即可引用。`
    try {
      brandAssets.value = await listBrandAssets()
    } catch {
      assetError.value = '已保存本次素材。完整列表读取失败，可重新打开素材库。'
    }
  } catch (error) {
    assetMessage.value = saved ? `已确认收藏 ${saved} 张。` : ''
    assetError.value = `${files[saved]?.name}：${normalizeApiError(error).detail}。可重新打开素材库核对后重试。`
  } finally {
    uploading.value = false
  }
}

async function useBrandAsset(asset: BrandAsset) {
  if (assetBusy.value) return
  assetError.value = ''
  if (selectedProductNames.value.has(asset.filename)) {
    const index = selectedProductImages.value.findIndex(item => item.filename === asset.filename)
    if (index >= 0) {
      URL.revokeObjectURL(selectedProductImages.value[index].preview)
      selectedProductImages.value.splice(index, 1)
      selectedProductNames.value.delete(asset.filename)
      selectedProductNames.value = new Set(selectedProductNames.value)
      emitProductImagesChange()
      assetMessage.value = '已取消本次引用，图片仍保存在素材库。'
    }
    return
  }
  if (selectedProductImages.value.length >= 12) {
    assetError.value = '本次最多引用 12 张产品图，请先取消一张。'
    return
  }
  readingAssets.value = true
  assetMessage.value = '正在读取所选产品图…'
  try {
    const file = await brandAssetToFile(asset)
    selectedProductImages.value.push({ file, preview: URL.createObjectURL(file), filename: asset.filename })
    selectedProductNames.value.add(asset.filename)
    selectedProductNames.value = new Set(selectedProductNames.value)
    emitProductImagesChange()
    assetMessage.value = '产品图已加入本次创作。'
  } catch (error) {
    assetMessage.value = ''
    assetError.value = '引用失败：' + normalizeApiError(error).detail
  } finally {
    readingAssets.value = false
  }
}

function emitProductImagesChange() {
  emit('productImagesChange', selectedProductImages.value.map(item => item.file))
}

function clearProductAssets() {
  assetMessage.value = ''
  selectedProductImages.value.forEach(item => URL.revokeObjectURL(item.preview))
  selectedProductImages.value = []
  selectedProductNames.value = new Set()
  emitProductImagesChange()
}

/**
 * 处理一键二创模式变化
 */
function handleLayoutMimicChange() {
  emit('layoutMimicChange', layoutMimicMode.value)
}

/**
 * 处理平台选择变化
 */
function handlePlatformChange() {
  emit('platformChange', selectedPlatform.value)
}

/**
 * 清理所有预览 URL
 */
function clearPreviews() {
  uploadedImages.value.forEach(img => URL.revokeObjectURL(img.preview))
  selectedProductImages.value.forEach(img => URL.revokeObjectURL(img.preview))
  uploadedImages.value = []
  selectedProductImages.value = []
  selectedProductNames.value = new Set()
  emitProductImagesChange()
  layoutMimicMode.value = false
}

// 组件卸载时清理
onUnmounted(() => {
  clearPreviews()
})

// 暴露方法给父组件
defineExpose({
  researchPanel,
  notePanel,
  preparationHint,
  clearPreviews
})
</script>

<style scoped>
/* 组合框容器 */
.composer-container {
  max-width: 960px;
  background: white;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.style-section {
  margin-top: 16px;
  text-align: left;
}

.asset-library {
  margin-top: 12px;
}

.asset-status, .asset-error {margin:6px 0;font-size:13px;overflow-wrap:anywhere}
.asset-error {color:#a92d28}
.asset-library-bar {
  display: flex;
  gap: 8px;
}

.asset-button {
  padding: 7px 11px;
  border: 1px solid #e5e5ea;
  border-radius: 9px;
  background: #fff;
  color: var(--text-sub);
  font-size: 12px;
  cursor: pointer;
}

.asset-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
  margin-top: 10px;
  padding: 10px;
  border-radius: 12px;
  background: #f7f7f8;
}

.asset-card {
  overflow: hidden;
  padding: 0;
  border: 1px solid transparent;
  border-radius: 9px;
  background: #fff;
  cursor: pointer;
}

.asset-card.selected {
  border-color: #074bbc;
  box-shadow: 0 0 0 2px rgba(7, 75, 188, 0.12);
}

.product-selection-summary {
  margin-top: 8px;
  color: #074bbc;
  font-size: 12px;
}

.clear-product-assets {
  border: 0;
  background: transparent;
  color: var(--text-sub);
  text-decoration: underline;
  cursor: pointer;
}

.asset-card:hover { border-color: var(--primary); }
.asset-card img { width: 100%; aspect-ratio: 1; object-fit: contain; display: block; }
.asset-card span { display: block; padding: 5px; font-size: 10px; }
.empty-assets { grid-column: 1 / -1; padding: 12px; color: var(--text-sub); font-size: 12px; }

.style-heading {display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px}
.style-heading h2 {margin:0;font-size:16px;line-height:1.5}
.style-grid {display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,148px),1fr));gap:8px}
.style-card {
  position:relative;display:grid;grid-row:span 3;grid-template-rows:subgrid;row-gap:5px;
  min-width:0;padding:12px;border:1px solid var(--border-color);border-radius:10px;
  background:#fff;cursor:pointer;overflow-wrap:anywhere;
}
.style-card:hover {border-color:#a5b7e5}
.style-card.selected {border-color:#315ac3;background:#f1f5ff;box-shadow:inset 0 0 0 1px #315ac3}
.style-card:focus-within {outline:2px solid #315ac3;outline-offset:2px}
.style-card input {position:absolute;top:14px;right:10px;width:14px;height:14px;accent-color:#315ac3}
.style-name {padding-right:15px;font-weight:650;font-size:13px;line-height:1.45}
.style-copy {font-size:12px;line-height:1.5;color:var(--text-sub)}
.style-meta {align-self:end;font-size:11px;color:#3052a2}
@media (max-width: 600px) {
  .composer-container {padding:12px}
  .composer-toolbar {flex-wrap:wrap;gap:8px}
  .style-grid {grid-template-columns:repeat(2,minmax(0,1fr))}
  .asset-grid {grid-template-columns:repeat(3,minmax(0,1fr))}
}
.style-description {
  display: block;
  margin-top: 6px;
  color: var(--text-sub);
  font-size: 11px;
  line-height: 1.35;
}

/* 输入区域 */
.composer-input-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.search-icon-static {
  flex-shrink: 0;
  padding-top: 8px;
  color: #999;
}

.composer-textarea {
  flex: 1;
  border: none;
  outline: none;
  font-size: 16px;
  line-height: 1.6;
  resize: none;
  min-height: 44px;
  max-height: 200px;
  padding: 8px 0;
  font-family: inherit;
  color: var(--text-main, #1a1a1a);
}

.composer-textarea::placeholder {
  color: #999;
}

.composer-textarea:disabled {
  background: transparent;
  color: #999;
}

/* 已上传图片预览 */
.uploaded-images-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 12px;
  align-items: center;
}

.uploaded-image-item {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.uploaded-image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-image-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  transition: opacity 0.2s;
}

.uploaded-image-item:hover .remove-image-btn {
  opacity: 1;
}

.remove-image-btn:hover {
  background: var(--primary, #ff2442);
}

.upload-hint {
  flex: 1;
  font-size: 12px;
  color: var(--text-sub, #666);
  text-align: right;
}

/* 一键二创选项 */
.layout-mimic-option {
  margin-top: 12px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #fff5f7 0%, #fff9fa 100%);
  border-radius: 12px;
  border: 1px solid rgba(255, 36, 66, 0.1);
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  user-select: none;
}

.checkbox-label input[type="checkbox"] {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.checkbox-custom {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border: 2px solid #ddd;
  border-radius: 6px;
  background: white;
  transition: all 0.2s;
  position: relative;
  margin-top: 2px;
}

.checkbox-label input[type="checkbox"]:checked + .checkbox-custom {
  background: var(--primary, #ff2442);
  border-color: var(--primary, #ff2442);
}

.checkbox-label input[type="checkbox"]:checked + .checkbox-custom::after {
  content: '';
  position: absolute;
  left: 6px;
  top: 2px;
  width: 4px;
  height: 9px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.checkbox-label input[type="checkbox"]:disabled + .checkbox-custom {
  opacity: 0.5;
  cursor: not-allowed;
}

.checkbox-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.option-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-main, #1a1a1a);
  display: flex;
  align-items: center;
  gap: 6px;
}

.option-title::before {
  content: '✨';
  font-size: 16px;
}

.option-desc {
  font-size: 12px;
  color: var(--text-sub, #666);
  line-height: 1.5;
}

/* 工具栏 */
.composer-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.toolbar-left {
  display: flex;
  gap: 8px;
}

/* 平台选择下拉框 */
.platform-select {
  height: 40px;
  padding: 0 16px;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
  background: white;
  color: #333;
  font-size: 14px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s;
  outline: none;
}

.platform-select:hover {
  border-color: var(--primary, #ff2442);
}

.platform-select:focus {
  border-color: var(--primary, #ff2442);
  box-shadow: 0 0 0 3px rgba(255, 36, 66, 0.1);
}

.platform-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #f5f5f5;
}

.tool-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #f5f5f5;
  border: none;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
}

.tool-btn:hover {
  background: #eee;
  color: var(--primary, #ff2442);
}

.tool-btn.active {
  background: rgba(255, 36, 66, 0.1);
  color: var(--primary, #ff2442);
}

.badge-count {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  background: var(--primary, #ff2442);
  color: white;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

/* 生成按钮 */
.generate-btn {
  min-width: 112px;
  padding: 10px 24px;
  font-size: 15px;
  border-radius: 100px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-hint {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(255, 36, 66, 0.06);
  color: var(--text-sub, #666);
  font-size: 14px;
  line-height: 1.5;
  text-align: right;
}

/* 加载动画 */
.spinner-sm {
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
