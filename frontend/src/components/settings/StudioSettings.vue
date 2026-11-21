<template>
  <section class="card studio">
    <h2>调研接口</h2>
    <label for="tikhub">TikHub API Key · {{ configured ? '已配置' : '待配置' }}</label>
    <input id="tikhub" v-model="key" type="password" autocomplete="new-password" placeholder="输入新密钥">
    <button class="btn" :disabled="busy || !key.trim()" @click="saveKey">保存密钥</button>
    <h2>CPA 图片模型优先顺序</h2>
    <label for="order">每行一个模型，首行优先</label>
    <textarea id="order" rows="4" v-model="order" />
    <div><button class="btn" :disabled="busy" @click="refresh">读取 CPA 模型目录</button>
    <button class="btn" :disabled="busy || !order.trim()" @click="saveOrder">保存顺序</button></div>
    <div v-if="catalog.length">点击追加模型
      <button class="btn" v-for="m in catalog" :key="m" :disabled="lines().includes(m)" @click="order=[...lines(),m].join('\n')">{{ m }}</button>
    </div>
    <p role="status">{{ message }}</p>
  </section>
</template>
<script setup lang="ts">
import {ref,onMounted} from 'vue'
import {loadStudio,saveStudio,discoverModels,studioError} from '../../api/studio'
const configured=ref(false), key=ref(''), order=ref(''), catalog=ref<string[]>([]), message=ref(''), busy=ref(false)
const lines=()=>order.value.split(/\s+/).filter(Boolean)
async function run(action:()=>Promise<void>){busy.value=true;message.value='';try{await action()}catch(e){message.value=studioError(e)}finally{busy.value=false}}
onMounted(()=>run(async()=>{const s=await loadStudio();configured.value=s.tikhub_configured;order.value=s.models.join('\n')}))
const refresh=()=>run(async()=>{catalog.value=await discoverModels();message.value='已从 CPA 读取当前目录'})
const saveKey=()=>run(async()=>{const s=await saveStudio({tikhub_key:key.value.trim()});configured.value=s.tikhub_configured;key.value='';message.value='密钥已保存'})
const saveOrder=()=>run(async()=>{await saveStudio({models:lines()});message.value='顺序已保存'})
</script>
<style scoped>
.studio{display:grid;gap:10px;justify-items:start}.studio input,.studio textarea{width:min(100%,34rem);padding:9px;border:1px solid #ccc;border-radius:8px}.studio h2{font-size:18px;margin-top:8px}.studio button{margin-right:6px}
</style>
