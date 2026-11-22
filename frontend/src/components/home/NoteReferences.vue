<template>
  <section class="note-references">
    <div class="note-heading">
      <label for="reference-note-url">小红书调研 <span>选填</span></label>
      <button type="button" :disabled="disabled || busy || !topic.trim()" @click="runStudy">{{ searching ? '正在调研…' : '按主题搜索笔记' }}</button>
    </div>
    <input id="reference-note-url" v-model="url" :disabled="disabled || busy" placeholder="有想参考的笔记？粘贴链接或 App 分享文字" maxlength="3000">
    <textarea v-if="url.trim() || excerpt" v-model="excerpt" :disabled="disabled || busy" rows="2" maxlength="3000"
      aria-label="笔记参考摘录" placeholder="可选：粘贴想参考的正文或要点，直接作为摘录使用"/>
    <button v-if="url.trim()" type="button" :disabled="disabled || busy" @click="add">
      {{ busy ? '读取中…' : excerpt.trim() ? '添加这段摘录' : '读取并添加笔记' }}
    </button>
    <small v-if="url.trim()">点击添加后，这篇笔记会参与本次创作。</small>
    <details v-if="study"><summary>{{study.basis}} · {{study.valid_count}} 条有效候选</summary>
      <ol><li v-for="n in study.notes" :key="n.id"><a :href="n.url" target="_blank" rel="noopener noreferrer">{{ n.title }}</a> · {{n.date}} · 赞 {{n.likes??'未知'}} / 藏 {{n.saves??'未知'}} {{study.selected.includes(n.id)?' · 入选':''}}</li></ol>
    </details>
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
import {computed, ref, watch} from 'vue'
import {readNote, searchNotes, studioError, type Study, type NoteReference} from '../../api/studio'
const props = defineProps<{disabled:boolean; topic:string}>()
const notes = ref<NoteReference[]>([])
const url = ref(''), excerpt = ref(''), error = ref(''), reading = ref(false)
const searching = ref(false)
const busy = computed(() => reading.value || searching.value)
const study = ref<Study|null>(null)
watch(() => props.topic.trim(), () => { study.value = null })
async function runStudy() {
  const keyword = props.topic.trim()
  if (!keyword || busy.value) return
  searching.value = true
  error.value = ''
  try {
    const result = await searchNotes(keyword)
    if (keyword === props.topic.trim()) study.value = result
  } catch (e) {
    if (keyword === props.topic.trim()) error.value = studioError(e)
  } finally {
    searching.value = false
  }
}
async function add() {
  error.value = ''
  const match = url.value.match(/https?:\/\/[^\s<>，。；、]+/i)
  try {
    const link = new URL((match?.[0] || '').replace(/[.,;!?）)\]]+$/, ''))
    if (!['xiaohongshu.com','www.xiaohongshu.com','xhslink.com','www.xhslink.com','xhslink.cn','www.xhslink.cn'].includes(link.hostname)
        || link.username || link.password || link.port || link.pathname === '/') throw new Error()
    if (notes.value.some(note => note.url === link.href)) { error.value = '这篇笔记已经添加'; return }
    if (notes.value.length >= 12) { error.value = '每次最多引用 12 篇笔记'; return }
    reading.value = true
    const note = excerpt.value.trim()
      ? {url:link.href, title:'', excerpt:excerpt.value.trim()}
      : await readNote(link.href)
    notes.value.push(note)
    url.value = ''
    excerpt.value = ''
  } catch (e) {
    error.value = busy.value ? studioError(e) : '请粘贴有效的小红书笔记链接或分享文字'
  } finally {
    reading.value = false
  }
}
defineExpose({notes,study,busy})
</script>
<style scoped>
.note-references {display:grid;gap:8px;text-align:left;margin:16px 0}
label {font-weight:600}
input,textarea {width:100%;box-sizing:border-box;padding:9px 12px;border:1px solid var(--border-color,#ddd);border-radius:8px;font:inherit}
button {justify-self:start;cursor:pointer}
ul {padding-left:20px;margin:0} li p {white-space:pre-line;max-height:7em;overflow:auto}
li button {margin-left:10px} p {font-size:13px;margin:0}

.note-heading {display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.note-heading label span {margin-left:5px;color:#626c7a;font-size:12px;font-weight:400}
button {width:auto;min-height:40px;padding:8px 12px;border:1px solid #cdd5e1;border-radius:8px;background:#fff;color:#23487f;font-family:inherit;font-size:14px;line-height:1.4}
button:hover:enabled {background:#f1f5ff}
button:disabled {color:#697383;cursor:default}
input,textarea {min-height:44px}
:where(button,input,textarea):focus-visible {outline:2px solid #315ac3;outline-offset:2px}
small {color:#546073}
details {overflow-wrap:anywhere;font-size:14px} details ol {max-height:220px;overflow:auto;padding-left:22px}
</style>
