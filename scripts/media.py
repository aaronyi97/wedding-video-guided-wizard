#!/usr/bin/env python3
"""Explicit, stage-bound text/TTS calls and local audio/video editing. No image generation."""
import argparse
import base64
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import uuid

# Support direct invocation and import-based tests without global installation.
spec=importlib.util.spec_from_file_location('wedding_wizard',Path(__file__).with_name('wizard.py'))
w=importlib.util.module_from_spec(spec); spec.loader.exec_module(w)

def binary(name):
    value=os.environ.get(name.upper()+'_BIN') or shutil.which(name)
    if not value: raise ValueError('缺少 '+name+'；请安装或设置 '+name.upper()+'_BIN 后继续当前步骤')
    return value

def run(args):
    result=subprocess.run([str(x) for x in args],capture_output=True,text=True)
    if result.returncode: raise ValueError('本地媒体命令失败：'+result.stderr[-1800:])
    return result.stdout

def probe(path):
    return json.loads(run([binary('ffprobe'),'-v','error','-show_format','-show_streams','-of','json',path]))

def duration(path): return float(probe(path)['format']['duration'])

def font_path():
    candidates=[os.environ.get('WEDDING_FONT',''),'/System/Library/Fonts/PingFang.ttc','/System/Library/Fonts/STHeiti Medium.ttc',
      '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc','C:/Windows/Fonts/msyh.ttc']
    return next((x for x in candidates if x and Path(x).is_file()),None)

def doctor():
    return {'python':sys.version.split()[0], 'ffmpeg':os.environ.get('FFMPEG_BIN') or shutil.which('ffmpeg'),
     'ffprobe':os.environ.get('FFPROBE_BIN') or shutil.which('ffprobe'),
     'pillow':importlib.util.find_spec('PIL') is not None,'chinese_font':font_path(),
     'kimi_configured':bool(os.environ.get('MOONSHOT_API_KEY')),
     'doubao_configured':bool(os.environ.get('DOUBAO_API_KEY') or (os.environ.get('DOUBAO_APP_ID') and os.environ.get('DOUBAO_ACCESS_KEY'))),
     'image_route':'external-gpt-manual-only','note':'配置存在不代表账号权限、余额或已授权付费调用'}

def stage(project,allowed):
    s=w.validate(project)
    if s['completed'] or s['current_step'] not in allowed: raise ValueError('当前步骤不允许此操作')
    return s

def new_output(project,path):
    p=w.inside(project,path,False)
    if p.exists(): raise ValueError('输出已存在，请用新的版本名')
    p.parent.mkdir(parents=True,exist_ok=True); return p

def new_outputs(project,path,suffixes):
    p=new_output(project,path)
    for suffix in suffixes:new_output(project,p.with_suffix(suffix))
    return p

def write_new(path,text):
    with Path(path).open('x',encoding='utf-8') as f:f.write(text)

def hashes(state,n):return {a['sha256'] for a in state['steps'][str(n)]['artifacts']}

def voice_selection(project,state,text,instructions,voice,rate,selection):
    p=w.inside(project,selection)
    if w.sha(p) not in hashes(state,4):raise ValueError('音色选择不是第4步确认版本')
    data=json.loads(p.read_text(encoding='utf-8'))
    script=w.inside(project,text);direction=w.inside(project,instructions)
    if w.sha(script) not in hashes(state,3) or w.sha(script)!=data['source_script_sha256']:
        raise ValueError('完整配音正文不是新人确认且试听选用的文案；修改需重新确认')
    if voice!=data['voice'] or rate!=data['rate'] or w.sha(direction)!=data['instructions_sha256']:
        raise ValueError('音色、语速或情绪指导与第4步选择不一致，先重新试听')

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): raise ValueError('拒绝携带凭据跟随接口重定向')

def request(url,headers,payload):
    data=json.dumps(payload,ensure_ascii=False).encode()
    req=urllib.request.Request(url,data=data,headers={**headers,'Content-Type':'application/json'},method='POST')
    try: return urllib.request.build_opener(NoRedirect).open(req,timeout=180)
    except Exception as e:
        code=getattr(e,'code',None)
        raise ValueError('生成请求未取得可验证结果'+('，HTTP '+str(code) if code else '')+'；先查状态，勿自动重复付费请求') from None

def kimi(project,prompt,out,authorized):
    stage(project,{2}); dest=new_output(project,out)
    text=w.inside(project,prompt).read_text(encoding='utf-8')
    if not authorized: raise ValueError('需当前任务明确授权文字 API 调用')
    key=os.environ.get('MOONSHOT_API_KEY')
    if not key: raise ValueError('未配置 MOONSHOT_API_KEY；使用写作包复制到 Kimi')
    base=os.environ.get('MOONSHOT_BASE_URL','https://api.moonshot.ai/v1').rstrip('/')
    if base not in ('https://api.moonshot.ai/v1','https://api.moonshot.cn/v1'):
        raise ValueError('内置适配仅支持官方 Kimi 地址；其他服务按用户确认的接口另行适配')
    payload={'model':os.environ.get('MOONSHOT_MODEL','kimi-k3'),'messages':[{'role':'user','content':text}], 'stream':False}
    with request(base+'/chat/completions',{'Authorization':'Bearer '+key},payload) as r: data=json.load(r)
    result=data['choices'][0]
    if result.get('finish_reason') not in ('stop',None): raise ValueError('文案未完整返回，请检查输出限制')
    body=result['message'].get('content')
    if not body: raise ValueError('未返回旁白正文')
    dest.write_text(body,encoding='utf-8'); return dest

def decode_tts(events):
    chunks=[]; ended=False; metadata=[]
    for e in events:
        code=e.get('code',0)
        if code not in (0,20000000): raise ValueError('语音服务返回错误码 '+str(code))
        if e.get('data'): chunks.append(base64.b64decode(e['data'],validate=True))
        if e.get('sentence'): metadata.append(e['sentence'])
        if code==20000000: ended=True
    data=b''.join(chunks)
    if not ended or not data: raise ValueError('语音流不完整或为空；不标记生成完成')
    return data,metadata

def tts(project,text_path,instructions,voice,rate,out,authorized,selection='VOICE_SELECTION.json'):
    state=stage(project,{4,5}); dest=new_outputs(project,out,['.timing.json'])
    if state['current_step']==5:voice_selection(project,state,text_path,instructions,voice,rate,selection)
    if dest.suffix.lower()!='.mp3': raise ValueError('此适配输出 MP3，请使用 .mp3 文件名')
    if not authorized: raise ValueError('需当前任务明确授权豆包 API 调用')
    text=w.inside(project,text_path).read_text(encoding='utf-8').strip()
    context=w.inside(project,instructions).read_text(encoding='utf-8').strip()
    if not text or not context or not -50<=rate<=100: raise ValueError('正文、情绪指导或语速无效')
    headers={'X-Api-Resource-Id':os.environ.get('DOUBAO_RESOURCE_ID','seed-tts-2.0'),'X-Api-Request-Id':str(uuid.uuid4())}
    if os.environ.get('DOUBAO_API_KEY'):headers['X-Api-Key']=os.environ['DOUBAO_API_KEY']
    elif os.environ.get('DOUBAO_APP_ID') and os.environ.get('DOUBAO_ACCESS_KEY'):
        headers.update({'X-Api-App-Id':os.environ['DOUBAO_APP_ID'],'X-Api-Access-Key':os.environ['DOUBAO_ACCESS_KEY']})
    else: raise ValueError('豆包配置缺失；本地配置密钥，不要贴到对话或仓库')
    payload={'user':{'uid':'wedding-video-wizard'},'req_params':{'text':text,'speaker':voice,
      'audio_params':{'format':'mp3','sample_rate':48000,'speech_rate':rate},
      'additions':json.dumps({'context_texts':[context],'enable_timestamp':True},ensure_ascii=False)}}
    with request('https://openspeech.bytedance.com/api/v3/tts/unidirectional',headers,payload) as r:
        events=[json.loads(line) for line in r if line.strip()]
    audio,metadata=decode_tts(events)
    dest.write_bytes(audio)
    write_new(dest.with_suffix('.timing.json'),json.dumps(metadata,ensure_ascii=False,indent=2))
    # Do not claim perceptual quality from provider status.
    return dest

def mix(project,voice,music,out,gain=.16,start=0,length=None):
    state=stage(project,{11,12}); dest=new_outputs(project,out,['.mix.json'])
    voice=w.inside(project,voice); music=w.inside(project,music)
    if w.sha(voice) not in hashes(state,5):raise ValueError('旁白不是第5步确认版本')
    settings={'kind':'wedding-mix-settings-v1','voice_sha256':w.sha(voice),'music_sha256':w.sha(music),'gain':gain}
    if state['current_step']==12:
        approved=[]
        for a in state['steps']['11']['artifacts']:
            if a['path'].endswith('.mix.json'):
                d=json.loads(w.inside(project,a['path']).read_text(encoding='utf-8'))
                approved.append({k:d.get(k) for k in settings})
        if settings not in approved:raise ValueError('声轨或音量不是第11步试听确认设置，先登记 .mix.json 或重听片段')
    total=duration(voice); music_total=duration(music)
    length=total-start if length is None else length
    if not all(math.isfinite(x) for x in (gain,start,length)) or not 0<gain<=1 or start<0 or length<=0 or start+length>total+.02:raise ValueError('音量或试听区间无效')
    if state['current_step']==12 and (start!=0 or abs(length-total)>.001):raise ValueError('第12步必须生成完整混音')
    if music_total+.02<start+length: raise ValueError('音乐长度不足，先安排延展或自然剪接；不能只补静音冒充完成')
    # Music arrangement supplies story dynamics; sidechain handles voice masking only.
    graph=f'[0:a]asplit=2[vo][side];[1:a]volume={gain}[bg];[bg][side]sidechaincompress=threshold=0.025:ratio=6:attack=20:release=350[duck];[vo][duck]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95,afade=t=out:st={max(0,length-1)}:d=1[a]'
    run([binary('ffmpeg'),'-v','error','-n','-ss',start,'-t',length,'-i',voice,'-ss',start,'-t',length,'-i',music,'-filter_complex',graph,'-map','[a]','-ar','48000','-ac','2',dest])
    write_new(dest.with_suffix('.mix.json'),json.dumps({**settings,'start':start,'length':length,'voice':voice.relative_to(Path(project).resolve()).as_posix(),'music':music.relative_to(Path(project).resolve()).as_posix()},ensure_ascii=False,indent=2))
    return dest

def validate_cues(cues,total):
    previous=0
    if not cues: raise ValueError('需要与主音轨对齐的字幕')
    for cue in cues:
        start,end=float(cue['start']),float(cue['end'])
        if not math.isfinite(start+end) or start<previous-.001 or end<=start or end>total+.02 or not str(cue['text']).strip():
            raise ValueError('字幕重叠、越界或为空')
        previous=end

def validate_timeline(shots,total,tolerance=.02):
    previous=0
    if not shots or not math.isfinite(total) or total<=0:raise ValueError('时间表为空或时长无效')
    for s in shots:
        start,end,src_in,src_out=map(float,[s['start'],s['end'],s['in'],s['out']])
        if not all(math.isfinite(x) for x in (start,end,src_in,src_out)):raise ValueError('非有限时间')
        if abs(start-previous)>.002 or end<=start or src_in<0 or src_out<=src_in:raise ValueError('时间表有空隙、重叠或无效区间')
        speed=(src_out-src_in)/(end-start)
        if not .5<=speed<=2:raise ValueError('变速过大，请重新安排镜头')
        previous=end
    if abs(previous-total)>tolerance:raise ValueError('时间表总长与主音轨不一致')

def stamp(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def captions(cues,width,height,folder,font):
    try: from PIL import Image, ImageDraw, ImageFont
    except ImportError:raise ValueError('字幕渲染缺少 Pillow；运行 python3 -m pip install Pillow 后继续')
    face=ImageFont.truetype(font,max(20,round(height*.05)))
    for i,cue in enumerate(cues):
        txt=str(cue['text']); lines=txt.splitlines()
        wrapped=[]
        for line in lines:
            while len(line)>18:wrapped.append(line[:18]);line=line[18:]
            if line:wrapped.append(line)
        if len(wrapped)>2:raise ValueError('字幕过长，请按实际语义拆成更短时间段')
        im=Image.new('RGBA',(width,height),(0,0,0,0));d=ImageDraw.Draw(im)
        text='\n'.join(wrapped)
        box=d.multiline_textbbox((0,0),text,font=face,stroke_width=2,spacing=6)
        tw,th=box[2]-box[0],box[3]-box[1]
        if tw>width*.88:raise ValueError('字幕超出安全区，缩短字幕或调整版式')
        d.multiline_text(((width-tw)/2-box[0],height-height*.08-th-box[1]),text,font=face,fill=(255,249,240,255),stroke_width=2,stroke_fill=(20,20,20,240),spacing=6,align='center')
        im.save(folder/f'cue-{i:03}.png')

def assemble(project,plan_path,out):
    state=stage(project,{13,14}); dest=new_outputs(project,out,['.srt','.qc.json'])
    plan=json.loads(w.inside(project,plan_path).read_text(encoding='utf-8'))
    audio=w.inside(project,plan['audio']);total=duration(audio)
    if w.sha(audio) not in {a['sha256'] for a in state['steps']['12']['artifacts']}:raise ValueError('主混音不是第12步确认版本')
    shots=plan['shots'];cues=plan['cues']
    storyboard=w.inside(project,plan['storyboard'])
    if w.sha(storyboard) not in hashes(state,6):raise ValueError('剪辑引用的分镜表不是第6步确认版本')
    expected=[s['id'] for s in json.loads(storyboard.read_text(encoding='utf-8'))['shots']]
    if not expected or len(expected)!=len(set(expected)) or [s.get('id') for s in shots]!=expected:
        raise ValueError('剪辑镜号缺失、重复或顺序与确认分镜不一致；改叙事先重新确认分镜')
    width,height,fps=plan.get('width',1920),plan.get('height',1080),plan.get('fps',24)
    if any(not isinstance(x,int) or x<=0 for x in (width,height,fps)) or width%2 or height%2:raise ValueError('画幅或帧率无效')
    validate_timeline(shots,total,tolerance=.5/fps+.000001);validate_cues(cues,total)
    if any(abs(t*fps-round(t*fps))>.01 for s in shots for t in (s['start'],s['end'])):raise ValueError('镜头切点必须对齐目标帧率')
    font=font_path()
    if not font:raise ValueError('缺少中文字体，请设置 WEDDING_FONT 为可用中文字体文件')
    allowed={a['sha256'] for a in state['steps']['9']['artifacts']}
    paths=[]
    for s in shots:
        v=w.inside(project,s['file']);paths.append(v)
        if w.sha(v) not in allowed:raise ValueError('视频不是第9步确认版本：'+v.name)
        if float(s['out'])>duration(v)+.02:raise ValueError('素材入出点超过实际视频')
    work=Path(project).resolve()/'work';work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='edit-',dir=work) as td:
        td=Path(td);parts=[]
        for i,(s,v) in enumerate(zip(shots,paths)):
            target=s['end']-s['start'];speed=(s['out']-s['in'])/target;part=td/f'{i:03}.mp4'
            vf=f'trim=start={s["in"]}:end={s["out"]},setpts=(PTS-STARTPTS)/{speed},scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps},format=yuv420p'
            run([binary('ffmpeg'),'-v','error','-n','-i',v,'-an','-vf',vf,'-t',target,'-c:v','libx264','-crf','18',part]);parts.append(part)
        (td/'concat.txt').write_text(''.join(f"file '{x.name}'\n" for x in parts))
        run([binary('ffmpeg'),'-v','error','-n','-f','concat','-safe','1','-i',td/'concat.txt','-c','copy',td/'picture.mp4'])
        captions(cues,width,height,td,font)
        # Bound inputs per render so long scripts do not exhaust file descriptors.
        previous=td/'picture.mp4'
        for batch in range(0,len(cues),12):
            selected=cues[batch:batch+12];args=[binary('ffmpeg'),'-v','error','-n','-i',previous]
            for j in range(len(selected)):args+=['-i',td/f'cue-{batch+j:03}.png']
            chain=[];last='0:v'
            for j,cue in enumerate(selected,1):
                nxt=f'v{j}';chain.append(f'[{last}][{j}:v]overlay=0:0:enable=\'gte(t,{cue["start"]})*lt(t,{cue["end"]})\'[{nxt}]');last=nxt
            target=td/f'sub-{batch}.mp4'
            run(args+['-filter_complex',';'.join(chain),'-map',f'[{last}]','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p',target]);previous=target
        run([binary('ffmpeg'),'-v','error','-n','-i',previous,'-i',audio,'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','256k','-ar','48000','-ac','2','-t',total,'-movflags','+faststart',dest])
    run([binary('ffmpeg'),'-v','error','-i',dest,'-f','null','-'])
    write_new(dest.with_suffix('.srt'),'\n\n'.join(f'{i}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i,c in enumerate(cues,1))+'\n')
    write_new(dest.with_suffix('.qc.json'),json.dumps({'technical':'decoded','media':probe(dest),'human_watch':'pending','couple_acceptance':'pending','source_plan_sha256':w.sha(w.inside(project,plan_path))},ensure_ascii=False,indent=2))
    return dest

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('doctor')
    q=sub.add_parser('probe');q.add_argument('file')
    for name in ('kimi','tts','mix','assemble'):
        q=sub.add_parser(name);q.add_argument('project',type=Path);q.add_argument('--out',required=True)
        if name=='kimi':q.add_argument('--prompt',required=True)
        if name=='tts':
            q.add_argument('--text',required=True);q.add_argument('--instructions',required=True);q.add_argument('--voice',required=True);q.add_argument('--rate',type=int,default=0)
            q.add_argument('--selection',default='VOICE_SELECTION.json')
        if name in ('kimi','tts'):q.add_argument('--authorized',action='store_true')
        if name=='mix':
            q.add_argument('--voice',required=True);q.add_argument('--music',required=True);q.add_argument('--gain',type=float,default=.16);q.add_argument('--start',type=float,default=0);q.add_argument('--length',type=float)
        if name=='assemble':q.add_argument('--plan',required=True)
    a=p.parse_args()
    if a.cmd=='doctor':print(json.dumps(doctor(),ensure_ascii=False,indent=2))
    elif a.cmd=='probe':print(json.dumps(probe(a.file),ensure_ascii=False,indent=2))
    elif a.cmd=='kimi':print(kimi(a.project,a.prompt,a.out,a.authorized))
    elif a.cmd=='tts':print(tts(a.project,a.text,a.instructions,a.voice,a.rate,a.out,a.authorized,a.selection))
    elif a.cmd=='mix':print(mix(a.project,a.voice,a.music,a.out,a.gain,a.start,a.length))
    else:print(assemble(a.project,a.plan,a.out))

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,KeyError,TypeError) as e:print('未完成：'+str(e),file=sys.stderr);sys.exit(2)
