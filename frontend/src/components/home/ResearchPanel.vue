<template>
  <section class="research">
    <div v-if="examples.length" class="examples">
      <a v-for="ex in examples" :key="ex.url" :href="ex.url" target="_blank" rel="noopener noreferrer">
        <img :src="ex.image" loading="lazy" alt=""><span>{{ex.caption}} · Pinterest ↗</span>
      </a>
    </div>
    <h3 v-if="!uploadCount">画面参考图</h3>
    <div class="actions">
      <button type="button" class="reference-action" :disabled="disabled || busy || !topic.trim()" v-if="glumoo && !uploadCount" @click="preview">按风格匹配六张</button>
      <button type="button" class="reference-action" :disabled="disabled || busy" v-if="!uploadCount" @click="browse">从参考库自选六张</button>
    </div>
    <p v-if="uploadCount">本次将使用 {{ uploadCount }} 张上传的参考图。</p>
    <p v-if="status" role="status">{{ status }}</p>
    <div v-if="browsing"><p>已选 {{draft.length}} / 6</p>
      <button type="button" class="reference-action" :disabled="draft.length!==6" @click="confirmPicks">使用这六张</button>
      <button type="button" class="reference-action" @click="browsing=false">取消</button>
      <div class="library"><button type="button" v-for="p in library" :key="p.id" :aria-pressed="draft.some(x=>x.id===p.id)" @click="toggle(p)"><img loading="lazy" :src="p.url+'?preview=1'" alt="选择参考图"></button></div>
    </div>
    <div v-if="!uploadCount" class="picks"><figure v-for="p in picks" :key="p.id"><img :src="p.url+'?preview=1'" loading="lazy" alt=""><figcaption>{{p.basis ? p.basis + ' · ' : ''}}{{p.reason}}</figcaption></figure></div>
  </section>
</template>
<script setup lang="ts">
import {ref,computed,watch} from 'vue'
import examplesData from '../../styleExamples.json'
import {listReferences,matchReferences,studioError,type Pick} from '../../api/studio'
const props=defineProps<{topic:string;styleId:string;disabled:boolean;uploadCount:number}>()
const glumoo=computed(()=>props.styleId.startsWith('glumoo'))
const examples=computed(()=>examplesData[props.styleId as keyof typeof examplesData]||[])
const picks=ref<Pick[]>([]),status=ref(''),busy=ref(false)
const browsing=ref(false),library=ref<Pick[]>([]),draft=ref<Pick[]>([])
const working = computed(() => busy.value || browsing.value)
async function browse(){
  busy.value=true
  try {
    if(!library.value.length) library.value=await listReferences()
    draft.value=[...picks.value]; browsing.value=true
  } catch(e) {status.value=studioError(e)} finally {busy.value=false}
}
function toggle(p:Pick){if(draft.value.some(x=>x.id===p.id))draft.value=draft.value.filter(x=>x.id!==p.id);else if(draft.value.length<6)draft.value.push({...p,reason:'手动选入本次参考',basis:'自选'})}
let manual=false
function confirmPicks(){manual=true;picks.value=[...draft.value];browsing.value=false;status.value='已采用自选的六张参考图'}
let revision=0
watch(()=>[props.topic.trim(),props.styleId],()=>{
  revision++
  if(!manual) picks.value=[]
  status.value=''
})
watch(()=>props.uploadCount,n=>{if(n) browsing.value=false})
async function find(){const id=revision;status.value='正在查看参考库图片并比较风格…';const result=await matchReferences(props.topic.trim(),props.styleId)
  if(id!==revision)throw Error('主题已变化，请重新匹配')
  manual=false;picks.value=result;status.value=result.length===6?'已为六页选好参考图':'库中有 '+result.length+' 张匹配，可从参考库自选六张或上传当次参考图'}
async function preview(){busy.value=true;try{await find()}catch(e){status.value=studioError(e)}finally{busy.value=false}}
async function selectedFiles(){
  if(busy.value)throw Error('调研仍在进行，请稍后再生成')
  if(picks.value.length!==6)throw Error("请先选好六张参考图")
  return Promise.all(picks.value.map(async p=>{const r=await fetch(p.url);if(!r.ok)throw Error('参考图读取失败，请重试')
    const blob=await r.blob();return new File([blob],p.id,{type:blob.type})}))
}
defineExpose({picks,selectedFiles,working})
</script>
<style scoped>.research{margin-top:12px}.actions,.examples,.picks{display:flex;gap:9px;flex-wrap:wrap}.examples a,.picks figure{margin:0;max-width:155px;font-size:12px}.examples img,.picks img{width:140px;height:95px;object-fit:contain;display:block}.research ol{max-height:200px;overflow:auto;padding-left:22px}.research p{font-size:13px}.library{display:grid;grid-template-columns:repeat(auto-fill,minmax(70px,1fr));max-height:280px;overflow:auto;gap:5px}.library img{width:100%;height:85px;object-fit:cover}.library button{padding:2px;border:2px solid transparent}.library button[aria-pressed=true]{border-color:#2259de}
.research {text-align:left;margin-top:20px}
.research h3 {font-size:15px;margin:0 0 8px}
.reference-action {display:inline-flex;align-items:center;justify-content:center;width:auto;min-height:44px;padding:9px 15px;border:1px solid #c9d4e9;border-radius:9px;background:#f6f8fc;color:#25436f;line-height:1.35;font-family:inherit;font-size:14px;font-weight:600;white-space:nowrap;cursor:pointer}
.reference-action:hover:enabled {background:#eaf0fe;border-color:#849fd5}
.reference-action:disabled {color:#636d7d;background:#f6f7f9;cursor:default}
.reference-action:focus-visible {outline:3px solid #4d77ce;outline-offset:2px}
</style>
