export type BookStatus = 'unfinished' | 'finished' | 'fully-tagged';

export type BookStatusInfo = {
  state: BookStatus;
  label: string;
  description: string;
  icon: string;
};

const STATUS_COPY: Record<BookStatus, BookStatusInfo> = {
  unfinished: {
    state: 'unfinished',
    label: 'Unfinished',
    description: 'The reading text is still being completed or translated.',
    icon: 'hourglass_empty'
  },
  finished: {
    state: 'finished',
    label: 'Finished',
    description: 'The reading text is complete; person and place tagging is absent, partial, or not yet audited end to end.',
    icon: 'check_circle'
  },
  'fully-tagged': {
    state: 'fully-tagged',
    label: 'Fully tagged',
    description: 'The reading text is complete and in-scope people and places have been audited with TEI registry references throughout.',
    icon: 'fact_check'
  }
};

const BOOK_STATUS_OVERRIDES: Record<string, BookStatus> = {
  'austen-jane/emma': 'fully-tagged',
  'mann-thomas/the-magic-mountain': 'unfinished',
  'tolstoy-leo/war-and-peace': 'unfinished'
};

export function bookStatusForSlugs(authorSlug: string, bookSlug: string): BookStatusInfo {
  const state = BOOK_STATUS_OVERRIDES[`${authorSlug}/${bookSlug}`] || 'finished';
  return STATUS_COPY[state];
}
