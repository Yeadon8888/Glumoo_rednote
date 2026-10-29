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
        @keydown.enter.prevent="handleEnter"
        :disabled="loading"
        rows="1"
      ></textarea>
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
        <button type="button" class="asset-button" @click="toggleAssetLibrary" :disabled="loading">
          品牌素材库 <span v-if="brandAssets.length">{{ brandAssets.length }}</span>
        </button>
        <label class="asset-button">
          上传并收藏
          <input type="file" accept="image/*" multiple hidden @change="handleBrandAssetUpload" />
        </label>
      </div>
      <div v-if="showAssetLibrary" class="asset-grid">
        <button
          v-for="asset in brandAssets"
          :key="asset.filename"
          type="button"
          class="asset-card"
          :class="{ selected: selectedProductNames.has(asset.filename) }"
          @click="useBrandAsset(asset)"
        >
          <img :src="asset.url" alt="品牌素材" />
          <span>点击引用</span>
        </button>
        <span v-if="brandAssets.length === 0" class="empty-assets">还没有素材，可上传产品图、Logo 或品牌参考图。</span>
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
    <div class="style-section">
      <div class="style-heading">选择内容风格</div>
      <div class="style-grid">
        <button
          v-for="style in contentStyles"
          :key="style.id"
          type="button"
          class="style-card"
          :class="{ active: store.contentStyle === style.id }"
          :disabled="loading"
          @click="store.setContentStyle(style.id)"
        >
          <span class="style-name">{{ style.name }}</span>
          <span v-if="style.badge" class="style-badge">{{ style.badge }}</span>
          <span class="style-description">{{ style.description }}</span>
        </button>
      </div>
      <div v-if="store.contentStyle.startsWith('glumoo')" class="glumoo-sop-hint">
        本次需上传恰好 6 张独立主参考图；产品图从上方品牌素材库单独选择。系统逐页只使用 1 张主参考与该页产品资产。
      </div>
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
          :disabled="!modelValue.trim() || loading"
        >
          <span v-if="loading" class="spinner-sm"></span>
          <span>{{ loading ? '生成中' : '生成大纲' }}</span>
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-hint" role="status" aria-live="polite">
      请稍后，这一步大概要 15-30 秒左右。
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { contentStyles } from '../../contentStyles'
import {
  brandAssetToFile,
  listBrandAssets,
  uploadBrandAssets,
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

// 一键二创模式
const layoutMimicMode = ref(false)

// 平台选择（从 store 同步初始值，确保与实际发送的值一致）
import { useGeneratorStore } from '../../stores/generator'
const store = useGeneratorStore()
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
 * 处理回车键
 */
function handleEnter(e: KeyboardEvent) {
  if (e.shiftKey) return // 允许 Shift+Enter 换行
  emit('generate')
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
  showAssetLibrary.value = !showAssetLibrary.value
  if (showAssetLibrary.value) {
    brandAssets.value = await listBrandAssets()
  }
}

async function handleBrandAssetUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files || []).slice(0, 8)
  if (files.length === 0) return
  await uploadBrandAssets(files)
  brandAssets.value = await listBrandAssets()
  showAssetLibrary.value = true
  target.value = ''
}

async function useBrandAsset(asset: BrandAsset) {
  if (selectedProductNames.value.has(asset.filename)) {
    const index = selectedProductImages.value.findIndex(item => item.filename === asset.filename)
    if (index >= 0) {
      URL.revokeObjectURL(selectedProductImages.value[index].preview)
      selectedProductImages.value.splice(index, 1)
      selectedProductNames.value.delete(asset.filename)
      selectedProductNames.value = new Set(selectedProductNames.value)
      emitProductImagesChange()
    }
    return
  }
  if (selectedProductImages.value.length >= 12) return
  const file = await brandAssetToFile(asset)
  selectedProductImages.value.push({
    file,
    preview: URL.createObjectURL(file),
    filename: asset.filename
  })
  selectedProductNames.value.add(asset.filename)
  selectedProductNames.value = new Set(selectedProductNames.value)
  emitProductImagesChange()
}

function emitProductImagesChange() {
  emit('productImagesChange', selectedProductImages.value.map(item => item.file))
}

function clearProductAssets() {
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
  clearPreviews
})
</script>

<style scoped>
/* 组合框容器 */
.composer-container {
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
.asset-card img { width: 100%; aspect-ratio: 1; object-fit: cover; display: block; }
.asset-card span { display: block; padding: 5px; font-size: 10px; }
.empty-assets { grid-column: 1 / -1; padding: 12px; color: var(--text-sub); font-size: 12px; }

.style-heading {
  margin-bottom: 8px;
  color: var(--text-sub);
  font-size: 13px;
  font-weight: 600;
}

.style-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
}

.style-card {
  min-height: 76px;
  padding: 10px;
  border: 1px solid #ececf0;
  border-radius: 12px;
  background: #fafafa;
  color: var(--text-main);
  text-align: left;
  cursor: pointer;
}

.style-card.active {
  border-color: var(--primary);
  background: rgba(255, 36, 66, 0.06);
  box-shadow: 0 0 0 1px rgba(255, 36, 66, 0.12);
}

.style-name {
  font-size: 13px;
  font-weight: 700;
}

.style-badge {
  float: right;
  color: var(--primary);
  font-size: 10px;
}

.style-description {
  display: block;
  margin-top: 6px;
  color: var(--text-sub);
  font-size: 11px;
  line-height: 1.35;
}

@media (max-width: 760px) {
  .style-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
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
