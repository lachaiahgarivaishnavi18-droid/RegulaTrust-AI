export const BASE = import.meta.env.VITE_API_URL || '';
let token = '';
export function setToken(value: string) { token = value; }
export async function api<T=any>(path:string, options:RequestInit={}):Promise<T> {
  const response=await fetch(BASE+'/api'+path,{...options,headers:{...(options.body && !(options.body instanceof FormData)?{'Content-Type':'application/json'}:{}),...(token?{Authorization:`Bearer ${token}`} : {}),...options.headers}});
  if(!response.ok){const data=await response.json().catch(()=>({detail:'Service unavailable'}));throw new Error(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail));}
  return response.json();
}
export async function download(id:string,format:string){const response=await fetch(`${BASE}/api/reports/${id}/download?format=${format}`,{headers:{Authorization:`Bearer ${token}`}});if(!response.ok){const data=await response.json();throw new Error(data.detail);}const url=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=url;a.download=`regulatrust-${id}.${format}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
