import pathlib

root=pathlib.Path.cwd()
renderer_path=root/'desktop'/'build'/'src'/'renderer.js'
renderer=renderer_path.read_text(encoding='utf-8')

old="function localRef(){const old=state.selected;state.selected=currentCode;const r=marketRef();state.selected=old;return r;}"
new="function localRef(){const cc=String(currentCode||'').toUpperCase();if(['HSI','HSIQ26','HSIU26'].includes(cc))return {region:'HK',code:'HSI'};const old=state.selected;state.selected=currentCode;const r=marketRef();state.selected=old;return r;}"
if old not in renderer:
    raise RuntimeError('localRef anchor missing')
renderer=renderer.replace(old,new,1)

old_draw="async function draw(resetView=false){if(loading)return;loading=true;const ref=localRef(),sy=localSymbol();if(!ref){box.innerHTML='<div class=\"chart-loading\">선택 종목의 시세 매핑이 없습니다.</div>';loading=false;return;}"
new_draw="async function draw(resetView=false){if(loading)return;loading=true;const ref=localRef(),sy=localSymbol();w.querySelector('#tvSymbolTitle').textContent=currentCode;w.querySelector('#tvTfLabel').textContent=({1:'1',2:'5',3:'15',4:'30',5:'60'}[currentK]||'1');w.querySelector('#tfTitle').textContent=({1:'1분',2:'5분',3:'15분',4:'30분',5:'1시간'}[currentK]||'1분');w.querySelector('#tvExchange').textContent=['HSI','HSIQ26','HSIU26'].includes(String(currentCode).toUpperCase())?'HKEX':(sy.exchange||'CME');if(!ref){box.innerHTML='<div class=\"chart-loading\">선택 종목의 시세 매핑이 없습니다.</div>';loading=false;return;}"
if old_draw not in renderer:
    raise RuntimeError('draw anchor missing')
renderer=renderer.replace(old_draw,new_draw,1)

renderer_path.write_text(renderer,encoding='utf-8')
check=renderer_path.read_text(encoding='utf-8')
for needle in ["return {region:'HK',code:'HSI'}", "?'HKEX':"]:
    if needle not in check:
        raise RuntimeError('missing HSI ref v26 patch: '+needle)
print('VELTRO v1.0.26 HSI marketRef routing fix applied')
