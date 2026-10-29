# Reader typography and illustration appearance

The online reader uses 20px text at the default size, 1.55 line spacing,
1.5em paragraph indents and no extra space between ordinary paragraphs.
Opening paragraphs and paragraphs following headings, scene breaks, quotations
or source figures are flush left. Empty source paragraphs and page markers do
not introduce phantom paragraph spacing or restart indentation.

Prose is justified with automatic hyphenation and a flush final line on wider
screens. At 600px and below it uses a ragged trailing edge to avoid large gaps
in narrow lines. Explicit source alignment, verse lineation, preformatted text,
letters and dramatic dialogue retain their separate rules. Chinese retains its
script-specific line spacing. Reader size, width and font controls still apply.
Internal TEI labels render as subheadings, and section milestones produce a
visible scene break. Quotations use inset text without the interface-style
vertical bar or muted color.

These choices follow the distinction between paragraph indents and paragraph
spacing in [Practical Typography](https://practicaltypography.com/first-line-indents.html)
and the [W3C paragraph indentation example](https://www.w3.org/Style/Examples/007/indent.en).
They affect HTML presentation only; canonical TEI, source wording and published
PDFs are unchanged. PDF export remains a separate publication command.

Engraving plates use grayscale inversion and screen blending in dark mode:
the original light paper becomes black and blends away, while the ink becomes
light. Light mode uses grayscale and multiply blending. Both retain the same
four-sided mask, without a white paper halo in dark mode. This treatment is
shared by Christie, Poe and Holmes; original source diagrams and approved
portraits are unaffected. Forced colors retain the unfiltered image.

Browser checks cover paragraph metrics, indentation after internal headings
and scene breaks, narrow-screen alignment, image blending in both appearances,
and the existing poetry, notes, language and reading-control workflows.
