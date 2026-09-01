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

# v1.0.40: keep the current Databento quote timer, but make the live candle roll over
# into a new timeframe bucket instead of freezing on the last historical candle.
renderer=renderer_path.read_text(encoding='utf-8')
fixed_refresh = r'''  async function refreshQuote(){
    if(isHsiCode())return;
    const ref=localRef(),sy=localSymbol();
    if(!ref)return;
    try{
      const qr=await window.desktop.getMarketQuote(ref),v=Number(qr?.quote?.ld);
      if(!(qr?.ok&&Number.isFinite(v)))return;
      lastEl.textContent=fmt(v,dec(sy));
      if(!candleSeries)return;
      const bucket=({1:1,2:5,3:15,4:30,5:60}[currentK]||1)*60000;
      let ts=Number(qr?.quote?.t);
      if(!Number.isFinite(ts)||ts<=0)ts=Date.now();
      else if(ts<1e12)ts*=1000;
      const bt=Math.floor(ts/bucket)*bucket;
      let b=lastBars.length?{...lastBars[lastBars.length-1]}:null;
      const prevBt=b?Math.floor(Number(b.t)/bucket)*bucket:null;
      if(!b||prevBt!==bt){
        b={t:bt,o:v,h:v,l:v,c:v,v:0};
        lastBars.push(b);
      }else{
        b.h=Math.max(Number(b.h)||v,v);
        b.l=Math.min(Number(b.l)||v,v);
        b.c=v;
        b.t=bt;
        lastBars[lastBars.length-1]=b;
      }
      candleSeries.update({time:Math.floor(bt/1000),open:b.o,high:b.h,low:b.l,close:b.c});
      if(volumeSeries)volumeSeries.update({time:Math.floor(bt/1000),value:Number(b.v)||0,color:b.c>=b.o?'rgba(239,83,80,.45)':'rgba(33,150,243,.45)'});
      showLastBar(b);
      conn.textContent='LIVE · DATABENTO';
      conn.classList.add('live');
    }catch(_e){}
  }
  try{await initMarketData();'''
pattern=r"  async function refreshQuote\(\)\{if\(isHsiCode\(\)\)return;.*?\n  try\{await initMarketData\(\);"
renderer,n=re.subn(pattern,fixed_refresh,renderer,count=1,flags=re.S)
if n!=1: raise RuntimeError('v1.0.40 live candle refresh anchor missing')
renderer_path.write_text(renderer,encoding='utf-8')

final_main=main_path.read_text(encoding='utf-8')
if marker not in final_main: raise RuntimeError('updater marker missing')
for required in ['setFeedURL','checkForUpdates','autoInstallOnAppQuit','quitAndInstall']:
    if required not in final_main: raise RuntimeError('updater runtime missing: '+required)
if pkg.get('build',{}).get('publish',[{}])[0].get('provider')!='github': raise RuntimeError('github publish provider missing')
final_renderer=renderer_path.read_text(encoding='utf-8')
for required in ['lastBars.push(b)','lastBars[lastBars.length-1]=b','LIVE · DATABENTO','else if(ts<1e12)ts*=1000']:
    if required not in final_renderer: raise RuntimeError('v1.0.40 chart fix missing: '+required)
print('VELTRO v1.0.40 updater and live candle rollover runtime verified')
