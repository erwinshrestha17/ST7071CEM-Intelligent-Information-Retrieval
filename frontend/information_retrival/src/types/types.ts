// src/types.ts
export type Page = 'SearchEngine' | 'DocumentClassifier';

// The values (a plain JS object)
export const Page = {
  SearchEngine: 'SearchEngine',
  DocumentClassifier: 'DocumentClassifier',
} as const;

export interface Publication {
  title?: string | null;
  authors?: string[] | null;
  date: string | null;
  abstract: string | null;
  publication: string | null;
  publicationYear: number | null;

  publication_link: string | null;
  relevanceScore: number | null;
}

export interface SearchResponse {
  total: number;
  publications: Publication[];
}

export interface SearchParams {
  query: string;
}