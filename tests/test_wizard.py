import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

class WizardTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('wizard', ROOT/'scripts/wizard.py')
        self.w = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.w)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Path(self.tmp.name)/'order'
        self.w.init(self.p)

    def artifact(self, name='稿.txt', text='合成测试资料，不是真实新人故事。'):
        p=self.p/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
        return p

    def pass_step(self, n):
        f=self.artifact(f'step{n}.txt')
        self.w.prepare(self.p,n,[f])
        self.w.approve(self.p,n,'couple' if n==3 else 'producer','合成测试：已核对此版本')

    def test_cannot_jump_or_confirm_without_artifacts(self):
        with self.assertRaises(ValueError): self.w.prepare(self.p,3,[self.artifact()])
        with self.assertRaises(ValueError): self.w.approve(self.p,1,'producer','同意')

    def test_couple_gate_and_no_blank_evidence(self):
        self.pass_step(1); self.pass_step(2)
        self.w.prepare(self.p,3,[self.artifact('script.txt')])
        with self.assertRaises(ValueError): self.w.approve(self.p,3,'producer','我觉得行')
        with self.assertRaises(ValueError): self.w.approve(self.p,3,'couple',' ')
        self.w.approve(self.p,3,'couple','合成测试：新人已确认全文v1')
        self.assertEqual(self.w.load(self.p)['current_step'],4)

    def test_changed_confirmed_file_blocks_advance(self):
        self.pass_step(1)
        (self.p/'step1.txt').write_text('发生变化')
        with self.assertRaises(ValueError): self.w.prepare(self.p,2,[self.artifact()])

    def test_reopen_preserves_unaffected_assets_and_confirmations(self):
        for n in range(1,13): self.pass_step(n)
        self.w.reopen(self.p,8,[9,13,14],'合成测试：只换第4镜')
        s=self.w.load(self.p)
        self.assertEqual(s['current_step'],8)
        self.assertEqual(s['steps']['10']['status'],'confirmed')
        self.assertTrue((self.p/'step8.txt').exists())
        self.assertEqual(s['steps']['9']['status'],'needs_review')

    def test_paths_cannot_escape_project(self):
        outside=Path(self.tmp.name)/'private.txt'; outside.write_text('private')
        with self.assertRaises(ValueError): self.w.prepare(self.p,1,[outside])
        (self.p/'link.txt').symlink_to(outside)
        with self.assertRaises(ValueError): self.w.prepare(self.p,1,[self.p/'link.txt'])

    def test_init_wont_overwrite(self):
        with self.assertRaises(ValueError): self.w.init(self.p)

    def test_header_and_final_dual_approval(self):
        for n in range(1,14): self.pass_step(n)
        self.w.prepare(self.p,14,[self.artifact('final.txt')])
        self.w.approve(self.p,14,'producer','合成测试：已核对正式片')
        self.assertFalse(self.w.load(self.p)['completed'])
        self.w.approve(self.p,14,'couple','合成测试：新人已验收')
        self.assertTrue(self.w.load(self.p)['completed'])
        self.assertIn('14/14',self.w.summary(self.p))

    def test_writing_pack_is_self_contained_and_wont_overwrite(self):
        self.pass_step(1)
        prompt=self.artifact('prompt.txt','任务：合成用例。\n事实：双方工作中相识。\n输出完整旁白。')
        out=self.p/'writing.zip'; self.w.writing_pack(self.p,prompt,out)
        with zipfile.ZipFile(out) as z:
            self.assertEqual(z.read('01-一键复制给Kimi-K3.txt').decode(),prompt.read_text())
            self.assertIn('00-使用说明.txt',z.namelist())
        with self.assertRaises(ValueError): self.w.writing_pack(self.p,prompt,out)

    def video_project(self):
        for n in range(1,6): self.pass_step(n)
        plan=self.artifact('SHOT_PLAN.json',json.dumps({'shots':[{'id':'S01'}]}))
        self.w.prepare(self.p,6,[plan]);self.w.approve(self.p,6,'producer','合成测试分镜确认')
        pic=self.p/'images/S01.png';pic.parent.mkdir(exist_ok=True);Image.new('RGB',(2,2),(160,170,180)).save(pic)
        self.w.prepare(self.p,7,[pic]);self.w.approve(self.p,7,'producer','合成测试试图确认')
        self.pass_step(8)
        prompt=self.artifact('prompts/S01-video.txt','首帧已经站定。缓缓抬眼，镜头轻推，保持身份，无配乐。')
        data={'plan':'SHOT_PLAN.json','shots':[{'id':'S01','image':'images/S01.png','prompt':'prompts/S01-video.txt'}]}
        return pic,prompt,data

    def test_video_zip_contains_actual_prompt_and_image(self):
        pic,prompt,data=self.video_project()
        manifest=self.artifact('VIDEO_PACK.json',json.dumps(data))
        out=self.w.video_pack(self.p,manifest,'video.zip')
        with zipfile.ZipFile(out) as z:
            self.assertEqual(z.read('S01/视频提示词.txt').decode(),prompt.read_text())
            self.assertEqual(z.read('S01/首帧参考图.png'),pic.read_bytes())

    def test_video_zip_rejects_approved_but_undecodable_image(self):
        pic,prompt,data=self.video_project()
        self.w.reopen(self.p,7,[8,9,13,14],'合成测试下载错误')
        pic.write_text('<html>下载失败</html>')
        self.w.prepare(self.p,7,[pic]);self.w.approve(self.p,7,'producer','合成测试：人为误把下载页确认')
        self.pass_step(8)
        manifest=self.artifact('VIDEO_PACK.json',json.dumps(data))
        with self.assertRaises(ValueError):self.w.video_pack(self.p,manifest,'bad.zip')

    def test_video_zip_rejects_wrong_shots_images_and_missing_prompt(self):
        pic,prompt,data=self.video_project()
        manifest=self.p/'VIDEO_PACK.json'
        for bad in (
            {'plan':'SHOT_PLAN.json','shots':[]},
            {'plan':'SHOT_PLAN.json','shots':data['shots']*2},
            {'plan':'SHOT_PLAN.json','shots':[{**data['shots'][0],'prompt':'missing.txt'}]},
            {'plan':'SHOT_PLAN.json','shots':[{**data['shots'][0],'image':'images/unapproved.png'}]}):
            self.artifact('images/unapproved.png','unapproved bytes')
            manifest.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):self.w.video_pack(self.p,manifest,'invalid.zip')
            self.assertFalse((self.p/'invalid.zip').exists())

    def test_image_route_never_uses_api(self):
        self.assertEqual(self.w.route('image',True),'external-gpt-manual')
        self.assertEqual(self.w.route('image-edit',True),'external-gpt-manual')
        self.assertEqual(self.w.route('voice',True),'api-if-authorized')

if __name__ == '__main__': unittest.main()
