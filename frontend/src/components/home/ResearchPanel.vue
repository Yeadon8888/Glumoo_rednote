<template>
  <section class="research">
    <div v-if="examples.length" class="examples">
      <a v-for="ex in examples" :key="ex.url" :href="ex.url" target="_blank" rel="noopener noreferrer">
        <img :src="ex.image" loading="lazy" alt=""><span>{{ex.caption}} · Pinterest ↗</span>
      </a>
    </div>
    <div class="actions">
      <button type="button" class="tool-btn" :disabled="disabled || busy || !topic.trim()" @click="runStudy">调研小红书笔记</button>
      <button type="button" class="tool-btn" :disabled="disabled || busy || !topic.trim()" @click="preview">按风格匹配参考库</button>
      <button type="button" class="tool-btn" :disabled="disabled || busy" @click="browse">从库中自选六张</button>
    </div>
    <p role="status">{{ status }}</p>
    <details v-if="study"><summary>{{study.basis}} · {{study.valid_count}} 条有效候选</summary>
      <ol><li v-for="n in study.notes" :key="n.id"><a :href="n.url" target="_blank" rel="noopener noreferrer">{{ n.title }}</a> · {{n.date}} · 赞 {{n.likes??'未知'}} / 藏 {{n.saves??'未知'}} {{study.selected.includes(n.id)?' · 入选':''}}</li></ol>
    </details>
    <div v-if="browsing"><p>已选 {{draft.length}} / 6</p>
      <button type="button" class="tool-btn" :disabled="draft.length!==6" @click="confirmPicks">使用这六张</button>
      <button type="button" class="tool-btn" @click="browsing=false">取消</button>
      <div class="library"><button type="button" v-for="p in library" :key="p.id" :aria-pressed="draft.some(x=>x.id===p.id)" @click="toggle(p)"><img loading="lazy" :src="p.url+'?preview=1'" alt="选择参考图"></button></div>
    </div>
    <div class="picks"><figure v-for="p in picks" :key="p.id"><img :src="p.url+'?preview=1'" loading="lazy" alt=""><figcaption>{{p.reason}}</figcaption></figure></div>
  </section>
</template>
<script setup lang="ts">
import {ref,computed,watch} from 'vue'
import examplesData from '../../styleExamples.json'
import {listReferences,matchReferences,searchNotes,studioError,type Study,type Pick} from '../../api/studio'
const props=defineProps<{topic:string;styleId:string;disabled:boolean}>()
const examples=computed(()=>examplesData[props.styleId as keyof typeof examplesData]||[])
const study=ref<Study|null>(null),picks=ref<Pick[]>([]),status=ref(''),busy=ref(false)
const browsing=ref(false),library=ref<Pick[]>([]),draft=ref<Pick[]>([])
async function browse(){try{if(!library.value.length)library.value=await listReferences();draft.value=[...picks.value];browsing.value=true}catch(e){status.value=studioError(e)}}
function toggle(p:Pick){if(draft.value.some(x=>x.id===p.id))draft.value=draft.value.filter(x=>x.id!==p.id);else if(draft.value.length<6)draft.value.push({...p,reason:'手动选入本次参考'})}
function confirmPicks(){picks.value=[...draft.value];browsing.value=false;status.value='已采用自选的六张参考图'}
let revision=0
watch(()=>[props.topic,props.styleId],()=>{revision++;browsing.value=false;picks.value=[];study.value=null;status.value=''})
async function runStudy(){const id=revision;busy.value=true;status.value='正在查询当期笔记…';try{const result=await searchNotes(props.topic.trim());if(id===revision){study.value=result;status.value=result.basis}}catch(e){if(id===revision)status.value=studioError(e)}finally{busy.value=false}}
async function find(){const id=revision;status.value='正在查看参考库图片并比较风格…';const result=await matchReferences(props.topic.trim(),props.styleId)
  if(id!==revision)throw Error('主题已变化，请重新匹配')
  picks.value=result;status.value=result.length===6?'已为六页选好参考图':'库中有 '+result.length+' 张匹配，请手动选择六张当次参考图'}
async function preview(){busy.value=true;try{await find()}catch(e){status.value=studioError(e)}finally{busy.value=false}}
async function selectedFiles(){
  if(busy.value)throw Error('调研仍在进行，请稍后再生成')
  if(picks.value.length!==6)await find()
  if(picks.value.length!==6)throw Error(status.value)
  return Promise.all(picks.value.map(async p=>{const r=await fetch(p.url);if(!r.ok)throw Error('参考图读取失败，请重试')
    const blob=await r.blob();return new File([blob],p.id,{type:blob.type})}))
}
defineExpose({study,picks,selectedFiles})
</script>
<style scoped>.research{margin-top:12px}.actions,.examples,.picks{display:flex;gap:9px;flex-wrap:wrap}.examples a,.picks figure{margin:0;max-width:155px;font-size:12px}.examples img,.picks img{width:140px;height:95px;object-fit:contain;display:block}.research ol{max-height:200px;overflow:auto;padding-left:22px}.research p{font-size:13px}.library{display:grid;grid-template-columns:repeat(auto-fill,minmax(70px,1fr));max-height:280px;overflow:auto;gap:5px}.library img{width:100%;height:85px;object-fit:cover}.library button{padding:2px;border:2px solid transparent}.library button[aria-pressed=true]{border-color:#2259de}</style>
