"""Regression examples from Gutenberg 21277, Richard II, act III scene III."""
import sys
import unittest
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tei'))
from build_gutenberg_drama_epub import speech_prefix, looks_like_stage


class FrenchDramaTest(unittest.TestCase):
    def test_parenthesized_directions_are_not_speeches(self):
        for text in (
            '(Fanfares.--Ils sortent.)',
            '(FANFARES.--Ils sortent.)',
            '(La trompette sonne pour demander un pourparler.--Richard paraît sur les remparts.)',
            '(LA TROMPETTE sonne pour demander un pourparler.--Richard paraît sur les remparts.)',
        ):
            element = etree.Element('p')
            element.text = text
            self.assertIsNone(speech_prefix(element))
            self.assertTrue(looks_like_stage(element, False))

    def test_real_speech_keeps_its_speaker_and_direction(self):
        element = etree.fromstring('<p>BOLINGBROKE, <i>à Northumberland</i>.--Que dit Sa Majesté?</p>')
        result = speech_prefix(element)
        self.assertIsNotNone(result)
        self.assertEqual(result[:2], ('BOLINGBROKE', 'à Northumberland'))


if __name__ == '__main__':
    unittest.main()
