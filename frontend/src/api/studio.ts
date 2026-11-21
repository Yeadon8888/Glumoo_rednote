import axios from 'axios'
const url = '/api/studio'
export interface NoteReference {url:string; title:string; excerpt:string}
export const readNote = async (urlValue:string) => (await axios.post<{note:NoteReference}>(url+'/research/note',{url:urlValue})).data.note
export interface Study {
  id: string
  basis: string
  valid_count: number
  notes: {id:string; title:string; likes:number|null; saves:number|null; date:string; url:string}[]
  selected: string[]
}
export interface Pick {id:string; url:string; reason:string; basis?:string}
export interface StudioSettings {tikhub_configured:boolean; models:string[]}
export const loadStudio = async () => (await axios.get<StudioSettings>(url+'/settings')).data
export const saveStudio = async (data: {tikhub_key?:string; models?:string[]}) => (await axios.put<StudioSettings>(url+'/settings',data)).data
export const discoverModels = async () => (await axios.get<{models:string[]}>(url+'/models')).data.models
export const searchNotes = async (topic:string) => (await axios.post<Study>(url+'/research',{topic})).data
export const matchReferences = async (topic:string,style:string) => (await axios.post<{items:Pick[]}>(url+'/references',{topic,style})).data.items
export const loadReview = async (id:string) => (await axios.get(url+'/reviews/'+id)).data.review
export const saveReview = async (id:string,score:number,reason:string,revision?:string) => (await axios.put(url+'/reviews/'+id,{score,reason,revision})).data.review
export const studioError = (e: unknown) => axios.isAxiosError(e) ? (e.response?.data?.error || '请求未完成，请重试') : '请求未完成，请重试'

export const listReferences = async () => (await axios.get<{items:Pick[]}>(url+'/reference-library')).data.items
