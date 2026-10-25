# Sherlock Holmes collections

The catalogue presents **The Complete Sherlock Holmes** and **The Chronological
Sherlock Holmes**. Both contain the same 63 works: the four novels, the 56
canonical short stories, Doyle’s two brief Holmes pieces (*The Field Bazaar*
and *How Watson Learned the Trick*), and *The Story of the Lost Special*.
The last is a related tale with an unnamed amateur reasoner; its association
with Holmes is identified rather than treated as an explicit appearance.

The original nine Holmes editions remain available at all of their existing
reader, TEI, and supplied PDF URLs. Their catalogue entries are replaced by
the two collections. *Tales of Terror and Mystery* remains available as a
separate collection, including its original copy of *The Lost Special*.

## Publication order

The complete collection uses the earliest recorded UK or US magazine issue,
including US appearances earlier than the familiar Strand issue. Novels
are placed at their first serial instalment and remain intact. The novel
chapters and retrospective narratives retain their internal reading order.
Dates retain their documented precision: a month is not assigned an invented
day. The date table is an editorial bibliography, not a claim to establish
the exact day each magazine issue reached every newsstand.

Publication dates are recorded in `tei/doyle/holmes/selection.json`, with
separate UK and US dates and the selected sorting date. The reference is the
[Arthur Conan Doyle Encyclopedia publication table](https://www.arthur-conan-doyle.com/wiki/The_62_Sherlock_Holmes_stories_written_by_Arthur_Conan_Doyle).
The [Lost Special source record](https://www.arthur-conan-doyle.com/wiki/The_Story_of_the_Lost_Special)
dates its first appearance to August 1898, rather than the 1922 compilation.
The impossible US date “31 September” for *The Abbey Grange* in the summary
table is corrected to 31 December 1904 from the dedicated story page’s
Collier’s illustration caption. Its earlier UK date still determines its
place in the collection.

## Career order

The companion follows [William S. Baring-Gould’s chronology](https://www.arthur-conan-doyle.com/wiki/William_Stuart_Baring-Gould).
This is a named editorial reconstruction: Doyle’s stories contain inconsistent
dates, and other chronologies differ. It begins with *The Gloria Scott* and
ends with *His Last Bow*. Novels are placed at their Holmes case dates;
earlier events narrated within them are not extracted into separate stories.

*The Lost Special* is placed at its disappearance on 3 June 1890, with its
later confession retained in the story. The two undated brief pieces are
placed during the Baker Street partnership, in 1890 and 1902 respectively.
Those placements are editorial approximations, not Baring-Gould dates.
The edition’s source description states these choices.

## Text and illustrations

`tei/build_holmes.py` explicitly assembles the editions from checksum-pinned
canonical TEI and the two short transcriptions stored in the selection
manifest. It does not alter its source files. Each source subtree receives
a distinct ID prefix, with local pointers remapped. Internal story sections
remain in the story; complete novels keep their chapter and part divisions.
The duplicate *Cardboard Box* in the source collections is included once.

Source responsibility statements, bibliographies, notes, and documentary
figures are retained. The importer compares the complete paragraph sequences,
notes, and documentary figure URLs against the original source subtrees and
records their counts and text hashes in `text-verification.json`.

There are 115 new engraving-style plates, one for each short story, novel
chapter, and epilogue. Both collections share those plates. Prompts and
generation provenance are recorded in `tei/doyle/holmes/illustrations.json`.
They use OpenAI’s built-in image generation and the Poe plate specification:
fine black parallel hatching, cross-hatching and stipple on ivory, landscape
composition, no captions or borders. JPEG plates up to 1200 pixels wide and
640-pixel previews are delivered under `tei/doyle/img/holmes/`; the reader applies
the same four-edge fade and appearance treatment as Poe.

`tei/prepare_holmes_art.py` prepares delivery formats from generated PNG
masters cached in the ignored `assets/source-holmes-art/` directory.
These offline preparation commands are separate from `npm run build`
and the site deployment. They do not generate PDFs. No collection PDF is
advertised unless one is explicitly published through the existing PDF
pipeline.
