import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from PIL import ImageFont

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('media',ROOT/'scripts/media.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);w=m.w

class LanguageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name)/'order'
        w.init(self.p)
    def test_english_summary_without_resetting_approved_work(self):
        f=self.p/'facts.txt';f.write_text('Synthetic test facts')
        w.prepare(self.p,1,[f]);w.approve(self.p,1,'producer','Synthetic approval')
        before=w.load(self.p)['steps']['1']
        w.set_language(self.p,'en')
        self.assertIn('Writing pack',w.summary(self.p));self.assertIn('12 steps remaining',w.summary(self.p))
        self.assertEqual(w.load(self.p)['steps']['1']['artifacts'],before['artifacts'])
        self.assertEqual(w.load(self.p)['steps']['1']['approvals'],before['approvals'])
        self.assertEqual(w.load(self.p)['content_language'],'zh')
    def test_english_pack_has_readable_names_and_instructions(self):
        w.set_language(self.p,'en');f=self.p/'facts.txt';f.write_text('Synthetic facts')
        w.prepare(self.p,1,[f]);w.approve(self.p,1,'producer','Synthetic approval')
        p=self.p/'prompt.txt';p.write_text('Write an English narration using only these confirmed facts.\nThe couple met at work.')
        out=w.writing_pack(self.p,p,'writing.zip')
        with zipfile.ZipFile(out) as z:
            self.assertEqual(z.read('01-Copy-to-Kimi-K3.txt').decode(),p.read_text())
            self.assertIn('couple',z.read('00-README.txt').decode())
    def test_english_captions_keep_words_and_fit_width(self):
        face=ImageFont.truetype(m.font_path('en'),24)
        original='Every ordinary afternoon became part of their story.'
        lines=m.caption_lines(original,face,400,'en')
        self.assertEqual(' '.join(lines),original)
        self.assertLessEqual(len(lines),2)
        self.assertTrue(all(face.getbbox(x)[2]<=400 for x in lines))
    def test_long_unbreakable_english_caption_rejected(self):
        face=ImageFont.truetype(m.font_path('en'),24)
        with self.assertRaises(ValueError):m.caption_lines('UnbreakableWord'*12,face,200,'en')
    def test_chinese_caption_limit_preserved(self):
        face=ImageFont.truetype(m.font_path() or m.font_path('en'),24)
        lines=m.caption_lines('甲'*25,face,600,'zh')
        self.assertEqual([len(x) for x in lines],[18,7])

if __name__=='__main__':unittest.main()
