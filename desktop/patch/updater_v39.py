import json, pathlib, re

root=pathlib.Path.cwd(); build=root/'desktop'/'build'
main_path=build/'src'/'main.js'; renderer_path=build/'src'/'renderer.js'; pkg_path=build/'package.json'
main=main_path.read_text(encoding='utf-8')

marker='// VELTRO_AUTO_UPDATER_V39'
if marker not in main:
    updater = r'''

// VELTRO_AUTO_UPDATER_V39
const { autoUpdater: veltroAutoUpdater } = require('electron-updater');
const veltroDialog = require('electron').dialog;
let veltroUpdatePromptOpen = false;
function veltroConfigureAutoUpdater(){
  if(!app.isPackaged) return;
  try{
    veltroAutoUpdater.autoDownload = true;
    veltroAutoUpdater.autoInstallOnAppQuit = true;
    veltroAutoUpdater.allowPrerelease = false;
    veltroAutoUpdater.allowDowngrade = false;
    veltroAutoUpdater.setFeedURL({provider:'github',owner:'dlxodnjs2456-hash',repo:'veltro',private:false});
    veltroAutoUpdater.on('error',(err)=>console.error('[updater]',err?.message||err));
    veltroAutoUpdater.on('update-available',(info)=>console.log('[updater] update available',info?.version));
    veltroAutoUpdater.on('update-not-available',(info)=>console.log('[updater] current',info?.version));
    veltroAutoUpdater.on('download-progress',(p)=>console.log('[updater] download',Math.round(Number(p?.percent||0))+'%'));
    veltroAutoUpdater.on('update-downloaded',async(info)=>{
      console.log('[updater] downloaded',info?.version);
      if(veltroUpdatePromptOpen) return;
      veltroUpdatePromptOpen = true;
      try{
        const result=await veltroDialog.showMessageBox({
          type:'info',
          buttons:['지금 재시작','나중에'],
          defaultId:0,
          cancelId:1,
          title:'VELTRO HTS 업데이트',
          message:`새 버전 v${info?.version||''} 업데이트가 준비되었습니다.`,
          detail:'지금 재시작하면 업데이트가 자동 적용됩니다.'
        });
        if(result.response===0) setTimeout(()=>veltroAutoUpdater.quitAndInstall(false,true),250);
      }catch(e){console.error('[updater] prompt',e?.message||e)}
      finally{veltroUpdatePromptOpen=false;}
    });
    const check=()=>veltroAutoUpdater.checkForUpdates().catch(e=>console.error('[updater] check',e?.message||e));
    setTimeout(check,3500);
    setInterval(check,15*60*1000);
  }catch(e){console.error('[updater] setup',e?.message||e)}
}
app.whenReady().then(()=>veltroConfigureAutoUpdater()).catch(()=>{});
'''
    main += updater

main_path.write_text(main,encoding='utf-8')

pkg=json.loads(pkg_path.read_text(encoding='utf-8-sig'))
pkg.setdefault('dependencies',{})['electron-updater']='^6.6.2'
build_cfg=pkg.setdefault('build',{})
build_cfg['publish']=[{'provider':'github','owner':'dlxodnjs2456-hash','repo':'veltro','releaseType':'release'}]
pkg_path.write_text(json.dumps(pkg,ensure_ascii=False,indent=2),encoding='utf-8')

# v1.0.41: historical bars remain Databento, while the currently forming candle and
# displayed last price use the exact same getMarketQuote response as the HTS quote state.
# The existing chart refresh cadence is preserved to avoid changing provider load behavior.
renderer=renderer_path.read_text(encoding='utf-8')

helper_anchor="  async function draw(resetView=false){"
helper=r'''  function applyUnifiedChartQuote(qr){
    if(!qr?.ok||!qr?.quote)return false;
    const sy=localSymbol(),v=Number(qr.quote.ld);
    if(!Number.isFinite(v)||v<=0)return false;
    try{if(typeof applyMarketQuoteToState==='function')applyMarketQuoteToState(currentCode,qr,false);}catch(_e){}
    lastEl.textContent=fmt(v,dec(sy));
    if(!candleSeries)return true;
    const bucket=({1:1,2:5,3:15,4:30,5:60}[currentK]||1)*60000;
    const now=Date.now();
    let bt=Math.floor(now/bucket)*bucket;
    let prev=lastBars.length?{...lastBars[lastBars.length-1]}:null;
    let prevBt=prev?Math.floor(Number(prev.t)/bucket)*bucket:null;
    if(prevBt!==null&&bt<prevBt)bt=prevBt;
    let b;
    if(!prev||prevBt!==bt){
      const open=prev&&Number.isFinite(Number(prev.c))?Number(prev.c):v;
      b={t:bt,o:open,h:Math.max(open,v),l:Math.min(open,v),c:v,v:0};
      lastBars.push(b);
    }else{
      b=prev;
      b.h=Math.max(Number(b.h)||v,v);
      b.l=Math.min(Number(b.l)||v,v);
      b.c=v;
      b.t=bt;
      lastBars[lastBars.length-1]=b;
    }
    candleSeries.update({time:Math.floor(bt/1000),open:b.o,high:b.h,low:b.l,close:b.c});
    if(volumeSeries)volumeSeries.update({time:Math.floor(bt/1000),value:Number(b.v)||0,color:b.c>=b.o?'rgba(239,83,80,.45)':'rgba(33,150,243,.45)'});
    showLastBar(b);
    const provider=String(qr?.provider||state.market?.provider||'MARKET').toUpperCase();
    conn.textContent='LIVE · '+provider;
    conn.classList.add('live');
    return true;
  }
'''
if helper_anchor not in renderer: raise RuntimeError('v1.0.41 draw anchor missing')
renderer=renderer.replace(helper_anchor,helper+helper_anchor,1)

old_after="buildChart(bars);showLastBar(bars[bars.length-1]);if(resetView)chart?.timeScale()?.fitContent();"
new_after="buildChart(bars);if(!applyUnifiedChartQuote(qr))showLastBar(bars[bars.length-1]);if(resetView)chart?.timeScale()?.fitContent();"
if old_after not in renderer: raise RuntimeError('v1.0.41 historical overwrite anchor missing')
renderer=renderer.replace(old_after,new_after,1)

refresh=r'''  async function refreshQuote(){
    if(isHsiCode())return;
    const ref=localRef();
    if(!ref)return;
    try{
      const qr=await window.desktop.getMarketQuote(ref);
      applyUnifiedChartQuote(qr);
    }catch(_e){}
  }
  try{await initMarketData();'''
pattern=r"  async function refreshQuote\(\)\{if\(isHsiCode\(\)\)return;.*?\n  try\{await initMarketData\(\);"
renderer,n=re.subn(pattern,refresh,renderer,count=1,flags=re.S)
if n!=1: raise RuntimeError('v1.0.41 live refresh anchor missing')

renderer_path.write_text(renderer,encoding='utf-8')

final_main=main_path.read_text(encoding='utf-8')
if marker not in final_main: raise RuntimeError('updater marker missing')
for required in ['setFeedURL','checkForUpdates','autoInstallOnAppQuit','quitAndInstall']:
    if required not in final_main: raise RuntimeError('updater runtime missing: '+required)
if pkg.get('build',{}).get('publish',[{}])[0].get('provider')!='github': raise RuntimeError('github publish provider missing')
final_renderer=renderer_path.read_text(encoding='utf-8')
for required in ['applyUnifiedChartQuote','applyMarketQuoteToState(currentCode,qr,false)','if(!applyUnifiedChartQuote(qr))showLastBar','applyUnifiedChartQuote(qr);']:
    if required not in final_renderer: raise RuntimeError('v1.0.41 unified chart fix missing: '+required)
print('VELTRO v1.0.41 quote/chart unification and live candle runtime verified')
