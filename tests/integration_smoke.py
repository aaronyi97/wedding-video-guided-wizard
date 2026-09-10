#!/usr/bin/env python3
"""Synthetic, no-API run through receipts, image/video ZIP, mixed audio and subtitles."""
import argparse
import importlib.util
import json
from pathlib import Path
import zipfile
from PIL import Image

spec=importlib.util.spec_from_file_location('media',Path(__file__).resolve().parents[1]/'scripts/media.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);w=m.w

def main(project):
    project=project.resolve()
    if project.exists():raise ValueError('Use a fresh output directory for synthetic tests')
    w.init(project)
    def text(name,body):
        p=project/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body,encoding='utf-8');return p
    def js(name,data):return text(name,json.dumps(data,ensure_ascii=False,indent=2))
    def accept(n,files):
        w.prepare(project,n,files);w.approve(project,n,'couple' if n==3 else 'producer','SYNTHETIC TEST ONLY: simulated approval, no real customer')
    facts=text('FACTS.md','Synthetic fixture. Two invented labels for software tests only. No customer data.')
    accept(1,[facts])
    prompt=text('WRITING_PROMPT.txt','仅用于软件检查的合成输入。\n任务：生成两句测试文字，非客户故事。')
    writing=w.writing_pack(project,prompt,'writing.zip')
    script=text('SCRIPT.txt','合成测试。字幕与声音只是测试素材。')
    accept(2,[writing,prompt,script]);accept(3,[script])
    direction=text('direction.txt','合成测试，不调用语音服务')
    selection=js('VOICE_SELECTION.json',{'voice':'synthetic','rate':0,'instructions':'direction.txt','instructions_sha256':w.sha(direction),'source_script':'SCRIPT.txt','source_script_sha256':w.sha(script)})
    accept(4,[selection,direction])
    voice=project/'voice.wav';music=project/'music.wav'
    for out,hz,vol in [(voice,440,.35),(music,220,.12)]:
        m.run([m.binary('ffmpeg'),'-v','error','-n','-f','lavfi','-i',f'sine=frequency={hz}:duration=6:sample_rate=48000','-af',f'volume={vol}','-ac','2',out])
    accept(5,[voice])
    plan=js('SHOT_PLAN.json',{'shots':[{'id':'S01','fact':'synthetic 1'},{'id':'S02','fact':'synthetic 2'}]})
    accept(6,[plan])
    images=[]
    for i,color in enumerate(['#445577','#a87868'],1):
        pic=project/f'S0{i}.png';Image.new('RGB',(640,360),color).save(pic);images.append(pic)
    accept(7,[images[0]]);accept(8,images)
    prompts=[text(f'S0{i}-video.txt',f'合成测试 S0{i}：保持首帧，轻微推近，无人声。') for i in (1,2)]
    manifest=js('VIDEO_PACK.json',{'plan':'SHOT_PLAN.json','shots':[{'id':f'S0{i}','image':images[i-1].name,'prompt':prompts[i-1].name} for i in (1,2)]})
    vp=w.video_pack(project,manifest,'videos.zip')
    with zipfile.ZipFile(vp) as z:
        assert z.read('S01/视频提示词.txt').decode()==prompts[0].read_text()
        assert z.read('S02/首帧参考图.png')==images[1].read_bytes()
    videos=[]
    for i,pic in enumerate(images,1):
        video=project/f'S0{i}.mp4';m.run([m.binary('ffmpeg'),'-v','error','-n','-loop','1','-i',pic,'-t','6','-r','24','-an','-c:v','libx264','-pix_fmt','yuv420p',video]);videos.append(video)
    accept(9,[vp,*videos]);accept(10,[music])
    excerpt=m.mix(project,voice,music,'sample.wav',start=1,length=2)
    accept(11,[excerpt,excerpt.with_suffix('.mix.json'),music])
    for args in [{'gain':.3},{'start':1,'length':2}]:
        try:m.mix(project,voice,music,'must-not-exist.wav',**args)
        except ValueError:pass
        else:raise AssertionError('Unapproved mix change was allowed')
    full=m.mix(project,voice,music,'full.wav');accept(12,[full,full.with_suffix('.mix.json')])
    data={'storyboard':'SHOT_PLAN.json','audio':'full.wav','width':640,'height':360,'fps':24,
        'shots':[{'id':f'S0{i}','file':video.name,'in':0,'out':3,'start':(i-1)*3,'end':i*3} for i,video in enumerate(videos,1)],
        'cues':[{'start':.25,'end':2.5,'text':'合成测试：第一段'},{'start':3.3,'end':5.75,'text':'第二段，字幕已烧录'}]}
    edl=js('EDIT_PLAN.json',data)
    bad={**data,'shots':[{**data['shots'][0],'out':6,'end':6}]}
    try:m.assemble(project,js('BAD_EDIT.json',bad),'omitted.mp4')
    except ValueError:pass
    else:raise AssertionError('Missing shot allowed')
    film=m.assemble(project,edl,'preview.mp4')
    meta=m.probe(film);v=next(s for s in meta['streams'] if s['codec_type']=='video');a=next(s for s in meta['streams'] if s['codec_type']=='audio')
    assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==(640,360,'24/1',144)
    assert a['sample_rate']=='48000' and a['channels']==2
    assert abs(m.duration(film)-6)<.05
    assert w.load(project)['current_step']==13
    qc=json.loads(film.with_suffix('.qc.json').read_text());assert qc['human_watch']=='pending'
    accept(13,[film,film.with_suffix('.srt'),film.with_suffix('.qc.json'),edl])
    final=m.assemble(project,edl,'final.mp4')
    w.prepare(project,14,[final,final.with_suffix('.srt'),edl]);w.approve(project,14,'producer','SYNTHETIC simulated producer check')
    assert not w.load(project)['completed']
    w.approve(project,14,'couple','SYNTHETIC simulated final acceptance');assert w.validate(project)['completed']
    screenshot=project/'subtitle-check.png';m.run([m.binary('ffmpeg'),'-v','error','-n','-ss','1','-i',film,'-frames:v','1',screenshot])
    report={'synthetic_only':True,'paid_calls':0,'frames':144,'seconds':6,'size':[640,360],'audio':'48kHz stereo','full_14_step_receipts':True,'writing_zip':True,'actual_image_video_prompt_zip':True,'mix_gate':True,'all_shots_required':True,'subtitles_burned':True,'human_status_not_auto_approved':True}
    js('TEST_REPORT.json',report);print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
