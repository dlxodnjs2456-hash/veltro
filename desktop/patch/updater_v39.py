import json, pathlib, re

root=pathlib.Path.cwd(); build=root/'desktop'/'build'
main_path=build/'src'/'main.js'; pkg_path=build/'package.json'
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

final_main=main_path.read_text(encoding='utf-8')
if marker not in final_main: raise RuntimeError('updater marker missing')
for required in ['setFeedURL','checkForUpdates','autoInstallOnAppQuit','quitAndInstall']:
    if required not in final_main: raise RuntimeError('updater runtime missing: '+required)
if pkg.get('build',{}).get('publish',[{}])[0].get('provider')!='github': raise RuntimeError('github publish provider missing')
print('VELTRO v1.0.39 updater runtime verified')
