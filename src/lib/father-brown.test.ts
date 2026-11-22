import { expect, it } from 'vitest';
import { getLibrary, localizedUnitHref } from './library';

const collections = {
  'the-innocence-of-father-brown': { stories: 12, first: 'The Blue Cross', last: 'The Three Tools of Death' },
  'the-wisdom-of-father-brown': { stories: 12, first: 'The Absence of Mr. Glass', last: 'The Fairy Tale of Father Brown' },
  'the-incredulity-of-father-brown': { stories: 8, first: 'The Resurrection of Father Brown', last: 'The Ghost of Gideon Wise' },
  'the-secret-of-father-brown': { stories: 10, first: 'The Secret of Father Brown', last: 'The Secret of Flambeau' },
};

it('adds the four public-domain Father Brown collections, one story per page', () => {
  const author = getLibrary().authors.find(item => item.slug === 'chesterton-g-k')!;
  for (const [slug, expected] of Object.entries(collections)) {
    const work = author.works.find(item => item.slug === slug)!;
    const edition = work.editions[0];
    const stories = edition.units.filter(unit => unit.path.startsWith('story-'));
    expect(stories).toHaveLength(expected.stories);
    expect(stories[0].title).toBe(expected.first);
    expect(stories.at(-1)!.title).toBe(expected.last);
    expect(edition.sourceLinks[0].href).toBe(`https://standardebooks.org/ebooks/g-k-chesterton/${slug}`);
    expect(edition.sourceCredits.join(' ')).toContain('Standard Ebooks');
    expect(localizedUnitHref(work, edition, stories[0])).toContain(`/en/authors/chesterton-g-k/${slug}/`);
  }
  const incredulity = author.works.find(item => item.slug === 'the-incredulity-of-father-brown')!.editions[0];
  expect(incredulity.units.slice(0, 2).map(unit => unit.title)).toEqual(['Dedication', 'Preface']);
});
