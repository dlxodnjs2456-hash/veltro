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

# v1.0.43: chart is read-only with respect to HTS trading/orderbook state.
# Historical candles come from the normal getMarketKline path. The forming candle
# uses only actual quote ticks. No previous-close bridging or artificial price adjustment.
renderer=renderer_path.read_text(encoding='utf-8')

helper_anchor="  async function draw(resetView=false){"
helper=r'''  function applyChartOnlyLiveQuote(qr){
    if(!qr?.ok||!qr?.quote)return false;
    const sy=localSymbol(),v=Number(qr.quote.ld);
    if(!Number.isFinite(v)||v<=0)return false;
    lastEl.textContent=fmt(v,dec(sy));
    if(!candleSeries)return true;
    const bucket=({1:1,2:5,3:15,4:30,5:60}[currentK]||1)*60000;
    let ts=Number(qr.quote.t);
    if(!Number.isFinite(ts)||ts<=0)ts=Date.now();
    else if(ts<1e12)ts*=1000;
    const bt=Math.floor(ts/bucket)*bucket;
    let prev=lastBars.length?{...lastBars[lastBars.length-1]}:null;
    const prevBt=prev?Math.floor(Number(prev.t)/bucket)*bucket:null;
    let b;
    if(!prev||prevBt!==bt){
      b={t:bt,o:v,h:v,l:v,c:v,v:0};
      lastBars.push(b);
    }else{
      b=prev;
      b.h=Math.max(Number(b.h)||v,v);
      b.l=Math.min(Number(b.l)||v,v);
      b.c=v;
      b.t=bt;
      lastBars[lastBars.length-1]=b;
    }
    try{candleSeries.update({time:Math.floor(bt/1000),open:b.o,high:b.h,low:b.l,close:b.c});}catch(_e){}
    if(volumeSeries){try{volumeSeries.update({time:Math.floor(bt/1000),value:Number(b.v)||0,color:b.c>=b.o?'rgba(239,83,80,.45)':'rgba(33,150,243,.45)'});}catch(_e){}}
    showLastBar(b);
    const provider=String(qr?.provider||'DATABENTO').toUpperCase();
    conn.textContent='LIVE · '+provider;
    conn.classList.add('live');
    return true;
  }
'''
if helper_anchor not in renderer: raise RuntimeError('v1.0.43 draw anchor missing')
renderer=renderer.replace(helper_anchor,helper+helper_anchor,1)

old_after="buildChart(bars);showLastBar(bars[bars.length-1]);if(resetView)chart?.timeScale()?.fitContent();"
new_after="buildChart(bars);if(!applyChartOnlyLiveQuote(qr))showLastBar(bars[bars.length-1]);if(resetView)chart?.timeScale()?.fitContent();"
if old_after not in renderer: raise RuntimeError('v1.0.43 historical display anchor missing')
renderer=renderer.replace(old_after,new_after,1)

refresh=r'''  async function refreshQuote(){
    if(isHsiCode())return;
    const ref=localRef();
    if(!ref)return;
    try{
      const qr=await window.desktop.getMarketQuote(ref);
      applyChartOnlyLiveQuote(qr);
    }catch(_e){}
  }
  try{await initMarketData();'''
pattern=r"  async function refreshQuote\(\)\{if\(isHsiCode\(\)\)return;.*?\n  try\{await initMarketData\(\);"
renderer,n=re.subn(pattern,refresh,renderer,count=1,flags=re.S)
if n!=1: raise RuntimeError('v1.0.43 live refresh anchor missing')

renderer_path.write_text(renderer,encoding='utf-8')

final_main=main_path.read_text(encoding='utf-8')
if marker not in final_main: raise RuntimeError('updater marker missing')
for required in ['setFeedURL','checkForUpdates','autoInstallOnAppQuit','quitAndInstall']:
    if required not in final_main: raise RuntimeError('updater runtime missing: '+required)
if pkg.get('build',{}).get('publish',[{}])[0].get('provider')!='github': raise RuntimeError('github publish provider missing')
final_renderer=renderer_path.read_text(encoding='utf-8')
for required in ['window.desktop.getMarketKline({...ref,kType:currentK,limit:3000})','applyChartOnlyLiveQuote','b={t:bt,o:v,h:v,l:v,c:v,v:0}','else if(ts<1e12)ts*=1000','quoteTimer=setInterval']:
    if required not in final_renderer: raise RuntimeError('v1.0.43 chart runtime missing: '+required)
for forbidden in ['databento-kline-test','applyMarketQuoteToState(currentCode,qr,false)']:
    if forbidden in final_renderer: raise RuntimeError('forbidden stale HTS chart behavior remains: '+forbidden)
print('VELTRO v1.0.43 production chart verified: real kline path, live timer, no price bridging, no orderbook mutation')
