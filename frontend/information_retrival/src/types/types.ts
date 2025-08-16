// src/types/types.ts

// The type definition (erasable)
export type Page = 'SearchEngine' | 'DocumentClassifier';

// The values (a plain JS object)
export const Page = {
  SearchEngine: 'SearchEngine',
  DocumentClassifier: 'DocumentClassifier',
} as const;

export interface Publication {
  title: string;
  authors: string[];
  publicationYear: number;
  publicationUrl: string;
  authorProfileUrl: string;
}
