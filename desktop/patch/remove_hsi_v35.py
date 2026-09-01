import pathlib,re

root=pathlib.Path.cwd()
renderer_path=root/'desktop'/'build'/'src'/'renderer.js'
renderer=renderer_path.read_text(encoding='utf-8')

# Hide HSI from every symbol list generated from state.symbols, while preserving
# the underlying symbol metadata so old records/positions can still render safely.
needle='Object.entries(state.symbols)'
replacement="Object.entries(state.symbols).filter(([code])=>!['HSI','HSIQ26','HSIU26'].includes(String(code).toUpperCase()))"
count=renderer.count(needle)
if count<1:
    raise RuntimeError('state.symbols list anchor missing')
renderer=renderer.replace(needle,replacement)

# If a previous local selection was HSI, fall back to NQ when opening the chart.
chart_anchor='async function renderChartWindow(w){'
if chart_anchor not in renderer:
    raise RuntimeError('chart window anchor missing')
renderer=renderer.replace(chart_anchor,chart_anchor+"\n  if(['HSI','HSIQ26','HSIU26'].includes(String(state.selected||'').toUpperCase())) state.selected='NQU26';",1)

# Runtime guard for any delayed/dynamic symbol controls outside the chart.
guard=r'''

/* v1.0.35: HSI removed from user-selectable HTS instruments only. */
(()=>{
  const blocked=new Set(['HSI','HSIQ26','HSIU26']);
  const clean=()=>{
    document.querySelectorAll('option').forEach(el=>{if(blocked.has(String(el.value||'').toUpperCase()))el.remove();});
    document.querySelectorAll('[data-symbol],[data-code]').forEach(el=>{
      const v=String(el.getAttribute('data-symbol')||el.getAttribute('data-code')||'').toUpperCase();
      if(blocked.has(v))el.remove();
    });
    document.querySelectorAll('select').forEach(el=>{
      if(blocked.has(String(el.value||'').toUpperCase())){
        const fallback=[...el.options].find(o=>!blocked.has(String(o.value||'').toUpperCase()));
        if(fallback)el.value=fallback.value;
      }
    });
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',clean,{once:true});else clean();
  try{new MutationObserver(clean).observe(document.documentElement,{childList:true,subtree:true});}catch{}
})();
'''
renderer += guard
renderer_path.write_text(renderer,encoding='utf-8')

check=renderer_path.read_text(encoding='utf-8')
if replacement not in check or 'v1.0.35: HSI removed' not in check:
    raise RuntimeError('HSI removal patch verification failed')
print(f'VELTRO v1.0.35 HSI selectable instrument removed ({count} state.symbols lists filtered)')
