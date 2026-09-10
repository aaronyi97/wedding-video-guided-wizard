#!/usr/bin/env python3
"""Portable project receipts and handoff ZIPs. Never generates images."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import zipfile

STEPS = ['故事采集','文案写作包与初稿','新人确认文案','配音音色试听','完整旁白',
         '分镜设计','三个重点分镜试图','剩余分镜生图','图生视频','BGM 风格试听',
         '配音与 BGM 片段','完整混音','带字幕预览','正式成片交付']
STATE='PROJECT_STATE.json'

def now(): return datetime.now(timezone.utc).isoformat()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def inside(project,path,existing=True):
    root=Path(project).resolve(); p=Path(path)
    if not p.is_absolute(): p=root/p
    p=p.resolve()
    try: p.relative_to(root)
    except ValueError: raise ValueError('文件必须在本单项目目录内：'+p.name)
    if existing and not p.is_file(): raise ValueError('缺少文件：'+p.name)
    return p

def save(project,state):
    root=Path(project).resolve()
    state['updated_at']=now()
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=root,delete=False) as f:
        json.dump(state,f,ensure_ascii=False,indent=2); f.write('\n'); tmp=f.name
    os.replace(tmp,root/STATE)

def init(project):
    root=Path(project).resolve()
    skill=Path(__file__).resolve().parents[1]
    if root==skill or skill in root.parents: raise ValueError('订单目录不能在 Skill 源码/安装目录内')
    if (root/STATE).exists(): raise ValueError('已有项目，请续做，不覆盖状态')
    root.mkdir(parents=True,exist_ok=True)
    s={'schema_version':1,'created_at':now(),'current_step':1,'completed':False,
       'steps':{str(i):{'name':n,'status':'not_started','artifacts':[], 'approvals':[]} for i,n in enumerate(STEPS,1)},'history':[]}
    save(root,s); return s

def load(project):
    s=json.loads((Path(project)/STATE).read_text(encoding='utf-8'))
    if s.get('schema_version')!=1 or set(s.get('steps',{}))!={str(n) for n in range(1,15)}:
        raise ValueError('状态结构不支持；不要重新初始化覆盖')
    if not isinstance(s.get('current_step'),int) or not 1<=s['current_step']<=14:
        raise ValueError('步骤编号无效')
    return s

def required(n): return {'couple'} if n==3 else {'producer','couple'} if n==14 else {'producer'}

def check_artifacts(project,record):
    if not record['artifacts']: raise ValueError('当前步骤尚未登记实际交付文件')
    for a in record['artifacts']:
        p=inside(project,a['path'])
        if sha(p)!=a['sha256']: raise ValueError('文件版本已变化，先 reopen 并重新确认：'+a['path'])

def validate(project,state=None):
    s=state or load(project)
    for k,r in s['steps'].items():
        if r['status']=='confirmed':
            check_artifacts(project,r)
            if not required(int(k))<={a['by'] for a in r['approvals'] if a['evidence'].strip()}:
                raise ValueError('确认依据不完整：'+k)
    expected=next((i for i in range(1,15) if s['steps'][str(i)]['status']!='confirmed'),14)
    if expected!=s['current_step']: raise ValueError('当前步骤与确认记录不一致')
    if s['completed']!=all(r['status']=='confirmed' for r in s['steps'].values()):
        raise ValueError('完成状态与确认记录不一致')
    return s

def advance(s):
    pending=[n for n in range(1,15) if s['steps'][str(n)]['status']!='confirmed']
    s['current_step']=pending[0] if pending else 14
    s['completed']=not pending

def current(project,n):
    s=validate(project)
    if s['completed'] or n!=s['current_step']: raise ValueError('只能操作当前步骤；修改旧成果先 reopen')
    return s

def prepare(project,n,files):
    s=current(project,n)
    if not files: raise ValueError('需要实际交付文件')
    paths=[inside(project,p) for p in files]
    if len(set(paths))!=len(paths): raise ValueError('重复文件')
    if any(p.name==STATE for p in paths): raise ValueError('状态文件不能作为交付证据')
    r=s['steps'][str(n)]
    if r['artifacts']: s['history'].append({'at':now(),'action':'replace-deliverable','step':n,'previous':r.copy()})
    r['artifacts']=[{'path':p.relative_to(Path(project).resolve()).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in paths]
    r['approvals']=[]; r['status']='awaiting_confirmation'
    save(project,s); return s

def approve(project,n,by,evidence):
    s=current(project,n); r=s['steps'][str(n)]
    if by not in required(n): raise ValueError('本步骤需要 '+','.join(sorted(required(n)))+' 的确认')
    if not evidence.strip(): raise ValueError('必须记录实际用户回复，不能空确认')
    check_artifacts(project,r)
    if any(a['by']==by for a in r['approvals']): raise ValueError('该角色已经确认；换版请重新 prepare')
    if n==14 and by=='couple' and not any(a['by']=='producer' for a in r['approvals']):
        raise ValueError('正式片先由制作方核对，再记录新人验收')
    r['approvals'].append({'at':now(),'by':by,'evidence':evidence.strip()})
    if required(n)<={a['by'] for a in r['approvals']}: r['status']='confirmed'
    advance(s); save(project,s); return s

def reopen(project,n,affected,reason):
    s=load(project)
    if not reason.strip() or not 1<=n<=14: raise ValueError('需要有效步骤和修改原因')
    ns=set(affected or range(n,15))|{n}
    if any(i<n or i>14 for i in ns): raise ValueError('受影响步骤范围错误')
    # Keep files and old receipts in history; only selected approvals become stale.
    for i in sorted(ns):
        r=s['steps'][str(i)]
        s['history'].append({'at':now(),'action':'reopen','step':i,'reason':reason,'previous':r.copy()})
        s['steps'][str(i)]={**r,'status':'needs_review','approvals':[]}
    advance(s); save(project,s); return s

def summary(project):
    s=validate(project); n=s['current_step']; r=s['steps'][str(n)]
    names={'not_started':'未开始','awaiting_confirmation':'待确认','needs_review':'需要修改','confirmed':'已确认'}
    status='新人已验收' if s['completed'] else names[r['status']]
    return f'【{n}/14｜{STEPS[n-1]}｜{status}｜后续还剩 {14-n} 步】'

def route(kind,configured=False):
    if kind in ('image','image-edit','character-image'): return 'external-gpt-manual'
    if kind not in ('writing','voice','video','music','editing'): raise ValueError('未知环节')
    return 'api-if-authorized' if configured else 'guided-manual-or-configure'

def zip_new(project,out,entries):
    out=inside(project,out,False)
    if out.exists(): raise ValueError('输出已存在，请使用新版本名')
    out.parent.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for name,data in entries.items():
        manifest.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    entries=dict(entries)
    entries['manifest.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    with tempfile.NamedTemporaryFile(dir=out.parent,delete=False) as f: tmp=Path(f.name)
    try:
        with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for name,data in entries.items(): z.writestr(name,data)
        with zipfile.ZipFile(tmp) as z:
            if z.testzip(): raise ValueError('压缩包完整性错误')
        # Exclusive output creation prevents overwriting even during a race.
        with out.open('xb') as dst,tmp.open('rb') as src:
            import shutil
            shutil.copyfileobj(src,dst)
    finally: tmp.unlink(missing_ok=True)
    return out

def writing_pack(project,prompt,out):
    current(project,2)
    p=inside(project,prompt); text=p.read_text(encoding='utf-8')
    if not text.strip() or re.search(r'\{\{[^}]+\}\}|\[待填\]|TODO',text):
        raise ValueError('写作包仍为空或包含未填占位符')
    return zip_new(project,out,{'00-使用说明.txt':'建议使用 Kimi K3。打开 01 文件，全选复制到 Kimi 对话，取得完整初稿后发回当前制作对话。先由制作方审稿，再发新人确认。\n'.encode(),
                              '01-一键复制给Kimi-K3.txt':text.encode()})

def video_pack(project,manifest,out):
    s=current(project,9)
    data=json.loads(inside(project,manifest).read_text(encoding='utf-8'))
    plan_path=inside(project,data['plan'])
    approved_plan={a['sha256'] for a in s['steps']['6']['artifacts']}
    if sha(plan_path) not in approved_plan: raise ValueError('镜头计划不是第6步确认版本')
    plan=json.loads(plan_path.read_text(encoding='utf-8'))
    expected=[str(x['id']) for x in plan['shots']]
    shots=data['shots']; ids=[str(x['id']) for x in shots]
    if not ids or len(set(ids))!=len(ids) or set(ids)!=set(expected) or len(set(expected))!=len(expected):
        raise ValueError('镜号重复、缺失或与确认计划不一致')
    approved={a['sha256'] for n in ('7','8') for a in s['steps'][n]['artifacts']}
    entries={'00-使用说明.txt':'每镜一个文件夹。上传本镜首帧图片，复制视频提示词，按提示词设置时长和画幅。确认模型入口能固定首帧；普通参考槽不一定等价。生成后完整自查，再按镜号发回当前对话。此包不授权自动生图。\n'.encode()}
    for shot in shots:
        ident=str(shot['id'])
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,48}',ident): raise ValueError('不安全的镜号')
        pic=inside(project,shot['image'])
        if pic.suffix.lower() not in ('.png','.jpg','.jpeg','.webp'): raise ValueError('不支持的首帧文件类型')
        if sha(pic) not in approved: raise ValueError('首帧不是已确认的第7/8步图片：'+ident)
        try:
            from PIL import Image
        except ImportError:raise ValueError('打包首帧需 Pillow 校验图片，请安装后继续当前步骤')
        try:
            with Image.open(pic) as im:im.verify()
            with Image.open(pic) as im:im.load()
        except Exception:raise ValueError('首帧不是可解码图片，先补回原图：'+ident) from None
        prompt=inside(project,shot['prompt']).read_text(encoding='utf-8')
        if not prompt.strip() or re.search(r'\{\{[^}]+\}\}|\[待填\]|TODO',prompt): raise ValueError('视频提示词为空或有占位符：'+ident)
        entries[f'{ident}/首帧参考图{pic.suffix.lower()}']=pic.read_bytes()
        entries[f'{ident}/视频提示词.txt']=prompt.encode()
    return zip_new(project,out,entries)

def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='cmd',required=True)
    for name in ('init','summary','validate'):
        q=sub.add_parser(name); q.add_argument('project',type=Path)
    q=sub.add_parser('prepare'); q.add_argument('project',type=Path); q.add_argument('--step',type=int,required=True); q.add_argument('--files',nargs='+',required=True)
    q=sub.add_parser('approve'); q.add_argument('project',type=Path); q.add_argument('--step',type=int,required=True); q.add_argument('--by',choices=['producer','couple'],required=True); q.add_argument('--evidence',required=True)
    q=sub.add_parser('reopen'); q.add_argument('project',type=Path); q.add_argument('--step',type=int,required=True); q.add_argument('--affected',nargs='*',type=int); q.add_argument('--reason',required=True)
    q=sub.add_parser('route'); q.add_argument('kind'); q.add_argument('--configured',action='store_true')
    for name,arg in [('writing-pack','prompt'),('video-pack','manifest')]:
        q=sub.add_parser(name); q.add_argument('project',type=Path); q.add_argument('--'+arg,required=True); q.add_argument('--out',required=True)
    a=p.parse_args()
    if a.cmd=='init': init(a.project); print(summary(a.project))
    elif a.cmd=='summary': print(summary(a.project))
    elif a.cmd=='validate': validate(a.project); print('状态与已确认文件一致')
    elif a.cmd=='prepare': prepare(a.project,a.step,a.files); print(summary(a.project))
    elif a.cmd=='approve': approve(a.project,a.step,a.by,a.evidence); print(summary(a.project))
    elif a.cmd=='reopen': reopen(a.project,a.step,a.affected,a.reason); print(summary(a.project))
    elif a.cmd=='route': print(route(a.kind,a.configured))
    elif a.cmd=='writing-pack': print(writing_pack(a.project,a.prompt,a.out))
    elif a.cmd=='video-pack': print(video_pack(a.project,a.manifest,a.out))

if __name__=='__main__':
    try: main()
    except (ValueError,OSError,KeyError,TypeError) as e:
        print('未执行：'+str(e),file=sys.stderr); sys.exit(2)
