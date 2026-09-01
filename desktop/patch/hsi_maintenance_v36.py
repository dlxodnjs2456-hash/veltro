import pathlib,re

root=pathlib.Path.cwd()
renderer_path=root/'desktop'/'build'/'src'/'renderer.js'
renderer=renderer_path.read_text(encoding='utf-8')

# Undo only the v1.0.35 visibility filter so HSI remains visible in symbol lists.
filtered="Object.entries(state.symbols).filter(([code])=>!['HSI','HSIQ26','HSIU26'].includes(String(code).toUpperCase()))"
if filtered not in renderer:
    raise RuntimeError('v1.0.35 HSI list filter anchor missing')
renderer=renderer.replace(filtered,'Object.entries(state.symbols)')

# Remove the v1.0.35 forced NQ fallback at chart open.
renderer=renderer.replace("\n  if(['HSI','HSIQ26','HSIU26'].includes(String(state.selected||'').toUpperCase())) state.selected='NQU26';",'',1)

# Remove the v1.0.35 runtime element-removal guard only.
renderer,n=re.subn(r"\n/\* v1\.0\.35: HSI removed from user-selectable HTS instruments only\. \*/\n\(\(\)=>\{.*?\n\}\)\(\);\n?",'\n',renderer,count=1,flags=re.S)
if n!=1:
    raise RuntimeError('v1.0.35 runtime HSI removal guard missing')

# Chart selector: show maintenance notice and keep the previous symbol; never start HSI data requests.
old_chart="w.querySelector('#proChartSymbol').onchange=e=>{closeRealtime();currentCode=e.target.value;state.selected=currentCode;lastBars=[];draw(true);startRealtime();};"
new_chart="w.querySelector('#proChartSymbol').onchange=e=>{const next=String(e.target.value||'').toUpperCase();if(['HSI','HSIQ26','HSIU26'].includes(next)){e.target.value=currentCode;alert('현재 점검중인 종목입니다.');return;}closeRealtime();currentCode=e.target.value;state.selected=currentCode;lastBars=[];draw(true);startRealtime();};"
if old_chart not in renderer:
    raise RuntimeError('chart symbol onchange anchor missing')
renderer=renderer.replace(old_chart,new_chart,1)

# Other HTS symbol controls/cards: intercept HSI selection globally, notify, and restore the previous select value.
guard=r'''

/* v1.0.36: HSI visible but temporarily unavailable. */
(()=>{
  const blocked=new Set(['HSI','HSIQ26','HSIU26']);
  const isBlocked=v=>blocked.has(String(v||'').toUpperCase());
  document.addEventListener('focusin',e=>{const el=e.target;if(el&&el.tagName==='SELECT')el.dataset.veltroPrevValue=el.value;},true);
  document.addEventListener('change',e=>{
    const el=e.target;if(!el||el.id==='proChartSymbol'||el.tagName!=='SELECT'||!isBlocked(el.value))return;
    const prev=el.dataset.veltroPrevValue;
    if(prev&&!isBlocked(prev))el.value=prev;
    else{const fallback=[...el.options].find(o=>!isBlocked(o.value));if(fallback)el.value=fallback.value;}
    e.preventDefault();e.stopImmediatePropagation();alert('현재 점검중인 종목입니다.');
  },true);
  document.addEventListener('click',e=>{
    const el=e.target?.closest?.('[data-symbol],[data-code]');if(!el)return;
    const v=el.getAttribute('data-symbol')||el.getAttribute('data-code')||'';
    if(!isBlocked(v))return;
    e.preventDefault();e.stopImmediatePropagation();alert('현재 점검중인 종목입니다.');
  },true);
})();
'''
renderer += guard
renderer_path.write_text(renderer,encoding='utf-8')

check=renderer_path.read_text(encoding='utf-8')
if filtered in check or 'v1.0.35: HSI removed' in check:
    raise RuntimeError('v1.0.35 HSI hiding behavior still remains')
if "alert('현재 점검중인 종목입니다.');" not in check or 'v1.0.36: HSI visible but temporarily unavailable.' not in check:
    raise RuntimeError('HSI maintenance notice guard missing')
print('VELTRO v1.0.36 HSI restored to lists with maintenance selection guard')
