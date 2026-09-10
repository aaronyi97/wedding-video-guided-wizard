import importlib.util
import unittest
from pathlib import Path
import base64
import json
import tempfile
from unittest.mock import patch

class MediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('media',Path(__file__).resolve().parents[1]/'scripts/media.py')
        cls.m=importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.m)
    def test_audio_stream_requires_end_and_payload(self):
        chunk={'code':0,'data':base64.b64encode(b'abc').decode()}
        with self.assertRaises(ValueError):self.m.decode_tts([chunk])
        with self.assertRaises(ValueError):self.m.decode_tts([{'code':20000000}])
        data,events=self.m.decode_tts([chunk,{'code':20000000}]);self.assertEqual(data,b'abc')
    def test_provider_error_is_not_success(self):
        with self.assertRaises(ValueError):self.m.decode_tts([{'code':55000000,'message':'secret details'}])
    def test_cues_cannot_overlap_or_overrun(self):
        self.m.validate_cues([{'start':0,'end':1,'text':'测试'}],2)
        for cues in [[{'start':0,'end':3,'text':'超时'}],[{'start':0,'end':1,'text':'一'},{'start':.5,'end':2,'text':'二'}]]:
            with self.assertRaises(ValueError):self.m.validate_cues(cues,2)
    def test_timeline_contiguous_and_speed_bounded(self):
        self.m.validate_timeline([{'start':0,'end':2,'in':0,'out':2}],2)
        with self.assertRaises(ValueError):self.m.validate_timeline([{'start':1,'end':2,'in':0,'out':1}],2)
        with self.assertRaises(ValueError):self.m.validate_timeline([{'start':0,'end':2,'in':0,'out':10}],2)
    def test_full_voice_rejects_unapproved_script_and_settings(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);m=self.m;w=m.w;w.init(p)
            script=p/'SCRIPT.txt';script.write_text('已确认的真实故事')
            direction=p/'direction.txt';direction.write_text('自然含笑')
            selected=p/'VOICE_SELECTION.json';selected.write_text(json.dumps({'voice':'A','rate':0,'instructions':'direction.txt','instructions_sha256':w.sha(direction),'source_script':'SCRIPT.txt','source_script_sha256':w.sha(script)}))
            for n in range(1,5):
                files=[script] if n==3 else [selected,direction] if n==4 else [script]
                w.prepare(p,n,files);w.approve(p,n,'couple' if n==3 else 'producer','合成测试确认')
            other=p/'other.txt';other.write_text('未确认的新情节')
            for text,voice,rate in [(other,'A',0),(script,'B',0),(script,'A',50)]:
                with patch.dict('os.environ',{'DOUBAO_API_KEY':'synthetic-not-a-real-key'}), patch.object(m,'request',side_effect=AssertionError('不应发起付费请求')):
                    with self.assertRaises(ValueError):m.tts(p,text,direction,voice,rate,'out.mp3',True)

    def test_frame_rounding_can_represent_any_audio_length(self):
        self.m.validate_timeline([{'start':0,'end':1,'in':0,'out':1}],1.0205,tolerance=.5/24+.000001)

    def test_sidecar_files_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'film.srt').write_text('keep old captions')
            with self.assertRaises(ValueError):self.m.new_outputs(p,'film.mp4',['.srt','.qc.json'])
            self.assertEqual((p/'film.srt').read_text(),'keep old captions')

    def test_mix_cannot_use_unapproved_voice(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);m=self.m;w=m.w;w.init(p);a=p/'a.txt';a.write_text('approved')
            for n in range(1,11):
                w.prepare(p,n,[a]);w.approve(p,n,'couple' if n==3 else 'producer','合成测试确认')
            voice=p/'unapproved.wav';voice.write_text('changed voice')
            with patch.object(m,'duration',side_effect=AssertionError('先校验版本')):
                with self.assertRaises(ValueError):m.mix(p,voice,a,'mixed.wav')

if __name__=='__main__':unittest.main()
