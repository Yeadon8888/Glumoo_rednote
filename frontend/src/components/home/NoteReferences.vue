<template>
  <section class="note-references">
    <label for="reference-note-url">小红书调研笔记</label>
    <input id="reference-note-url" v-model="url" :disabled="disabled || busy" placeholder="粘贴小红书笔记链接或 App 分享文字" maxlength="3000">
    <textarea v-if="url.trim() || excerpt" v-model="excerpt" :disabled="disabled || busy" rows="2" maxlength="3000"
      aria-label="笔记参考摘录" placeholder="可选：粘贴想参考的正文或要点，直接作为摘录使用"/>
    <button v-if="url.trim()" type="button" :disabled="disabled || busy" @click="add">
      {{ busy ? '读取中…' : excerpt.trim() ? '添加这段摘录' : '读取并添加笔记' }}
    </button>
    <p v-if="error" role="alert">{{ error }}</p>
    <ul v-if="notes.length">
      <li v-for="note in notes" :key="note.url">
        <a :href="note.url" target="_blank" rel="noopener noreferrer">{{ note.title || '已添加的笔记摘录' }}</a>
        <button type="button" :disabled="disabled" @click="notes = notes.filter(n => n.url !== note.url)">移除</button>
        <p v-if="note.excerpt">{{ note.excerpt }}</p>
      </li>
    </ul>
  </section>
</template>
<script setup lang="ts">
import {computed, ref} from 'vue'
import {readNote, studioError, type NoteReference} from '../../api/studio'
defineProps<{disabled:boolean}>()
const notes = ref<NoteReference[]>([])
const url = ref(''), excerpt = ref(''), error = ref(''), busy = ref(false)
const pending = computed(() => !!(busy.value || url.value.trim() || excerpt.value.trim()))
async function add() {
  error.value = ''
  const match = url.value.match(/https?:\/\/[^\s<>，。；、]+/i)
  try {
    const link = new URL((match?.[0] || '').replace(/[.,;!?）)\]]+$/, ''))
    if (!['xiaohongshu.com','www.xiaohongshu.com','xhslink.com','www.xhslink.com','xhslink.cn','www.xhslink.cn'].includes(link.hostname)
        || link.username || link.password || link.port || link.pathname === '/') throw new Error()
    if (notes.value.some(note => note.url === link.href)) { error.value = '这篇笔记已经添加'; return }
    if (notes.value.length >= 12) { error.value = '每次最多引用 12 篇笔记'; return }
    busy.value = true
    const note = excerpt.value.trim()
      ? {url:link.href, title:'', excerpt:excerpt.value.trim()}
      : await readNote(link.href)
    notes.value.push(note)
    url.value = ''
    excerpt.value = ''
  } catch (e) {
    error.value = busy.value ? studioError(e) : '请粘贴有效的小红书笔记链接或分享文字'
  } finally {
    busy.value = false
  }
}
defineExpose({notes,pending})
</script>
<style scoped>
.note-references {display:grid;gap:8px;text-align:left;margin:16px 0}
label {font-weight:600}
input,textarea {width:100%;box-sizing:border-box;padding:9px 12px;border:1px solid var(--border-color,#ddd);border-radius:8px;font:inherit}
button {justify-self:start;cursor:pointer}
ul {padding-left:20px;margin:0} li p {white-space:pre-line;max-height:7em;overflow:auto}
li button {margin-left:10px} p {font-size:13px;margin:0}
</style>
