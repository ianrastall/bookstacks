import type en from './locales/en';

// A plural message selects a CLDR category with Intl.PluralRules; `#` is the formatted count.
export type Plural = { other: string } & Partial<Record<'zero' | 'one' | 'two' | 'few' | 'many', string>>;
// String messages substitute `{0}` with an argument, or `{0|key}` with the plural message `key` for that argument.
export type Message = string | Plural;
export type MessageKey = keyof typeof en;
export type Messages = Record<MessageKey, Message>;
