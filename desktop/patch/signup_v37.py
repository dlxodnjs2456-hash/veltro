import pathlib,re

root=pathlib.Path.cwd()
build=root/'desktop'/'build'
renderer_path=build/'src'/'renderer.js'
styles_path=build/'src'/'styles.css'
main_path=build/'src'/'main.js'
preload_path=build/'src'/'preload.js'

renderer=renderer_path.read_text(encoding='utf-8')
if 'v1.0.37: signup entry' not in renderer:
    renderer += r'''

/* v1.0.37: signup entry only; existing login/auth flow remains unchanged. */
(()=>{
  const addSignup=()=>{
    if(document.getElementById('veltroSignupBtn')) return true;
    let login=document.getElementById('loginBtn');
    if(!login) login=[...document.querySelectorAll('button')].find(b=>String(b.textContent||'').trim()==='로그인');
    if(!login) return false;
    const btn=document.createElement('button');
    btn.id='veltroSignupBtn';
    btn.type='button';
    btn.textContent='회원가입';
    btn.onclick=()=>{try{window.desktop?.openSignup?.();}catch{}};
    login.insertAdjacentElement('afterend',btn);
    return true;
  };
  if(!addSignup()){
    const mo=new MutationObserver(()=>{if(addSignup())mo.disconnect();});
    mo.observe(document.documentElement,{childList:true,subtree:true});
  }
})();
'''
renderer_path.write_text(renderer,encoding='utf-8')

styles=styles_path.read_text(encoding='utf-8')
if '#veltroSignupBtn' not in styles:
    styles += r'''

/* v1.0.37 signup button */
#veltroSignupBtn{width:100%!important;min-height:42px!important;margin-top:8px!important;border:1px solid #3d86bb!important;border-radius:4px!important;background:#fff!important;color:#1474b5!important;font-weight:700!important;cursor:pointer!important}
#veltroSignupBtn:hover{background:#edf7fe!important}
'''
styles_path.write_text(styles,encoding='utf-8')

main=main_path.read_text(encoding='utf-8')
# Ensure Electron shell is available without altering the existing imports otherwise.
m=re.search(r"const\s*\{([^}]+)\}\s*=\s*require\(['\"]electron['\"]\);",main)
if not m:
    raise RuntimeError('electron import anchor missing')
parts=[x.strip() for x in m.group(1).split(',') if x.strip()]
if 'shell' not in parts:
    parts.append('shell')
    repl="const { " + ', '.join(parts) + " } = require('electron');"
    main=main[:m.start()]+repl+main[m.end():]
if "app:open-signup" not in main:
    anchor="ipcMain.handle('app:quit',()=>app.quit());"
    if anchor not in main:
        raise RuntimeError('app:quit handler anchor missing')
    main=main.replace(anchor,anchor+"\nipcMain.handle('app:open-signup',()=>shell.openExternal('https://veltro-n8v3.vercel.app/signup.html'));",1)
main_path.write_text(main,encoding='utf-8')

preload=preload_path.read_text(encoding='utf-8')
if 'openSignup:' not in preload:
    anchor="quit: () => ipcRenderer.invoke('app:quit'),"
    if anchor not in preload:
        raise RuntimeError('preload quit anchor missing')
    preload=preload.replace(anchor,anchor+"\n  openSignup: () => ipcRenderer.invoke('app:open-signup'),",1)
preload_path.write_text(preload,encoding='utf-8')

check_r=renderer_path.read_text(encoding='utf-8')
check_m=main_path.read_text(encoding='utf-8')
check_p=preload_path.read_text(encoding='utf-8')
if 'veltroSignupBtn' not in check_r or '회원가입' not in check_r:
    raise RuntimeError('signup renderer injection missing')
if "app:open-signup" not in check_m or "openSignup:" not in check_p:
    raise RuntimeError('signup IPC bridge missing')
print('VELTRO v1.0.37 signup button patch applied')
