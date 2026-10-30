"""Shared movement fixtures and real publication layout regressions."""
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET
import re

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from drama_layout import DramaLayout,stage_clone
from build_exports import LatexRenderer,parse_edition


class DramaLayoutTests(unittest.TestCase):
    def test_full_corpus_preserves_text_and_order(self):
        paths=list((ROOT/'tei/shakespeare').glob('*.xml'))
        self.assertGreaterEqual(len(paths),85)
        for path in paths:
            root=ET.parse(path).getroot()
            before=re.sub(r'\s+','',''.join(root.itertext()))
            language={'eng':'en','fra':'fr','spa':'es'}[path.stem[-3:]]
            DramaLayout(path,language).prepare(root)
            self.assertEqual(re.sub(r'\s+','',''.join(root.itertext())),before,path.name)
    def test_shared_classifications(self):
        files={'en':'shakespeare_a-midsummer-nights-dream_eng.xml','fr':'shakespeare_a-midsummer-nights-dream_fra.xml','es':'shakespeare_as-you-like-it_spa.xml'}
        layouts={lang:DramaLayout(ROOT/'tei/shakespeare'/file,lang) for lang,file in files.items()}
        for case in json.loads((ROOT/'tests/fixtures/drama-layout.json').read_text(encoding='utf-8')):
            stage=ET.Element('stage',type=case['declared']);stage.text=case['text']
            self.assertEqual(layouts[case['language']].kind(stage),case['expected'],case['text'])

    def test_real_entrances_exits_and_names(self):
        renderer=LatexRenderer(parse_edition(ROOT/'tei/shakespeare/shakespeare_a-midsummer-nights-dream_eng.xml'))
        body=renderer.render()
        self.assertIn(r'\bookstacksentrance{Enter \textnormal{THESEUS}',body)
        self.assertIn(r'\bookstacksexit{Exit \textnormal{PHILOSTRATE}',body)

    def test_direct_speech_directions_are_inline(self):
        edition=parse_edition(ROOT/'tei/shakespeare/shakespeare_the-two-noble-kinsmen_fra.xml')
        body=LatexRenderer(edition).render()
        self.assertIn(r'\bookstacksinlinestage{à \textnormal{THÉSÉE}.}',body)
        self.assertNotIn(r'\begin{bookstacksstage}',body)

    def test_source_delimiters_and_notes_survive(self):
        stage=ET.fromstring('<stage>(Exit <name>Theseus</name>.)<ref target="#note">1</ref></stage>')
        result=stage_clone(stage)
        self.assertEqual(''.join(result.itertext()),'Exit Theseus.1')
        self.assertEqual(result.find('ref').get('target'),'#note')
        self.assertEqual(''.join(stage.itertext()),'(Exit Theseus.)1')

    def test_joined_exit_and_entrance_become_separate_cues(self):
        layout=DramaLayout(ROOT/'tei/shakespeare/shakespeare_a-midsummer-nights-dream_fra.xml','fr')
        root=ET.fromstring('<TEI xmlns="http://www.tei-c.org/ns/1.0"><div><stage type="entrance">(Ils se retirent.)<lb/><lb/>(Entre Thésée.)</stage></div></TEI>')
        layout.prepare(root)
        self.assertEqual([s.get('data-bookstacks-stage-kind') for s in root.iter('{http://www.tei-c.org/ns/1.0}stage')],['exit','entrance'])

    def test_singular_action_stays_with_its_speaker(self):
        layout=DramaLayout(ROOT/'tei/shakespeare/shakespeare_a-midsummer-nights-dream_fra.xml','fr')
        root=ET.fromstring('<TEI xmlns="http://www.tei-c.org/ns/1.0"><div><sp><speaker>Thésée</speaker><p>Parlons.</p></sp><stage type="business">(Il se lève.)</stage><stage type="business">(On entend des cors.)</stage></div></TEI>')
        layout.prepare(root)
        paragraph=next(root.iter('{http://www.tei-c.org/ns/1.0}p'))
        self.assertIn('Il se lève.',''.join(paragraph.itertext()))
        self.assertEqual(root[0][-1].get('data-bookstacks-stage-kind'),'business')


if __name__=='__main__':unittest.main()
