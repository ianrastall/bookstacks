"""Regression checks for the standalone PDF exporter (no TeX required)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_exports as exports
from stage_release_assets import release_tag


class ScarletExportTests(unittest.TestCase):
    def setUp(self):
        self.edition = exports.parse_edition(ROOT / "tei/doyle/doyle_a-study-in-scarlet_eng.xml")

    def test_nested_closing_verse_is_preserved(self):
        body = exports.LatexRenderer(self.edition).render()
        first = body.index("Populus me sibilat, at mihi plaudo")
        second = body.index("Ipse domi simul ac nummos contemplor in arca.")
        self.assertLess(first, second)
        self.assertIn(r"\begin{verse}", body)

    def test_contents_include_chapters_within_parts(self):
        document = exports.latex_document(self.edition, "", "regular.otf", "italic.otf", "bold.otf", "bolditalic.otf")
        self.assertIn(r"\setcounter{tocdepth}{1}", document)
        body = exports.LatexRenderer(self.edition).render()
        self.assertEqual(body.count(r"\addcontentsline{toc}{section}"), 14)

    def test_paper_palette_is_applied_after_cover(self):
        previous = exports.PDF_THEME
        try:
            exports.PDF_THEME = "paper"
            document = exports.latex_document(self.edition, "", "regular.otf", "italic.otf", "bold.otf", "bolditalic.otf")
            self.assertGreater(document.index(r"\definecolor{booknight}{HTML}{FFFFFF}"), document.index("BOOKSTACKS CLASSICS"))
        finally:
            exports.PDF_THEME = previous

    def test_paired_exports_cannot_overwrite_each_other(self):
        previous_theme, previous_both = exports.PDF_THEME, exports.EXPORT_BOTH_THEMES
        try:
            exports.EXPORT_BOTH_THEMES = True
            exports.PDF_THEME = "paper"
            light_path = self.edition.output_dir / self.edition.output_name
            light_manifest = self.edition.manifest_path
            exports.PDF_THEME = "dark"
            dark_path = self.edition.output_dir / self.edition.output_name
            self.assertNotEqual(light_path, dark_path)
            self.assertTrue(light_path.name.endswith('_eng-light.pdf'))
            self.assertTrue(dark_path.name.endswith('_eng-dark.pdf'))
            self.assertNotEqual(light_manifest, self.edition.manifest_path)
        finally:
            exports.PDF_THEME, exports.EXPORT_BOTH_THEMES = previous_theme, previous_both

    def test_release_groups_accept_themed_filenames(self):
        for suffix in ('', '-light', '-dark'):
            self.assertEqual(release_tag(Path(f'doyle/edition/doyle_a-study-in-scarlet_eng{suffix}.pdf')), 'publications-en-a-m')
            self.assertEqual(release_tag(Path(f'austen/edition/austen_emma_fra{suffix}.pdf')), 'publications-fr')

    def test_uncommon_punctuation_and_math_keep_visible_glyphs(self):
        self.assertIn('―', exports.latex_escape('―'))
        self.assertIn('☛', exports.latex_escape('☛'))
        self.assertIn(r'\ne', exports.latex_escape('≠'))
        self.assertIn(r'\nobreak{}', exports.latex_escape('\u2060'))

    def test_incidental_han_preserves_western_apostrophe_metrics(self):
        edition = exports.parse_edition(ROOT / 'tei/doyle/doyle_the-chronological-sherlock-holmes_eng.xml')
        self.assertTrue(exports.needs_cjk(edition))
        document = exports.latex_document(edition, '', 'regular.otf', 'italic.otf', 'bold.otf', 'bolditalic.otf')
        self.assertIn(r'\xeCJKDeclareCharClass{Default}{"2018,"2019,"201C,"201D}', document)

    def test_chinese_retains_its_punctuation_classes(self):
        self.edition.locale = 'zh-Hans'
        self.edition.root.text = '汉'
        document = exports.latex_document(self.edition, '', 'regular.otf', 'italic.otf', 'bold.otf', 'bolditalic.otf')
        self.assertIn(r'\usepackage[AutoFallBack=true]{xeCJK}', document)
        self.assertNotIn(r'\xeCJKDeclareCharClass{Default}', document)


if __name__ == "__main__":
    unittest.main()
