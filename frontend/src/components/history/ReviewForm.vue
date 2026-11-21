<template>
  <details class="review"><summary>成品点评{{ previous ? ' · 已有点评' : '' }}</summary>
    <div v-if="previous">最近一次 · {{previous.score ? previous.score + ' / 5 分' : (previous.rating==='good'?'好':'差')}} · {{ previous.reason }} · {{ new Date(previous.reviewed_at).toLocaleString() }}</div>
    <label>作品评分 <select v-model="score"><option :value="0" disabled>请选择</option>
      <option v-for="(label, i) in ['差','较差','一般','好','很好']" :key="label" :value="i+1">{{ i+1 }} 分 · {{ label }}</option>
    </select></label>
    <textarea aria-label="点评理由" v-model="reason" maxlength="2000" rows="2" placeholder="哪一页、哪个细节影响了你的判断？"/>
    <button class="btn" :disabled="busy || !score || !reason.trim()" @click="save">保存对当前成品的点评</button>
    <p role="status">{{ message }}</p>
  </details>
</template>
<script setup lang="ts">
import {ref,onMounted} from 'vue'
import {loadReview,saveReview,studioError} from '../../api/studio'
const props=defineProps<{id:string;revision?:string}>()
const score=ref(0),reason=ref(''),busy=ref(true),message=ref('')
const previous=ref<{score?:number;rating:string;reason:string;reviewed_at:string}|null>(null)
onMounted(async()=>{try{previous.value=await loadReview(props.id)}catch(e){message.value=studioError(e)}finally{busy.value=false}})
async function save(){busy.value=true;try{previous.value=await saveReview(props.id,score.value,reason.value,props.revision);message.value='点评与本次成品已保存'}catch(e){message.value=studioError(e)}finally{busy.value=false}}
</script>
<style scoped>.review{margin-top:8px}.review summary{cursor:pointer;color:#2657a0}.review textarea{display:block;width:min(100%,32rem);margin:7px 0;padding:7px}.review select{margin:5px}.review p{font-size:13px}</style>
