// src/components/search-engine.tsx

import React, { useState, useMemo } from 'react';
import { Loader2, ExternalLink } from "lucide-react";

import { searchPublications } from '../services/information-retrival-service';

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Publication } from "@/types/types.ts";

const ITEMS_PER_PAGE = 10;
const ABSTRACT_CHAR_LIMIT = 300; // A good character limit to approximate 5 lines

// --- UI IMPROVEMENT: Helper function for dynamic badge colors based on score ---
const getScoreBadgeVariant = (score: number | undefined | null): 'destructive' | 'secondary' | 'default' => {
  if (score === null || score === undefined) return 'secondary';
  if (score >= 0.8) return 'default';
  if (score >= 0.5) return 'secondary';
  return 'destructive';
};

// --- NEW: Extracted Card component for better state management ---
interface PublicationCardProps {
  publication: Publication;
}

const PublicationCard: React.FC<PublicationCardProps> = ({ publication: pub }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const isLongAbstract = pub.abstract && pub.abstract.length > ABSTRACT_CHAR_LIMIT;

    const abstractText = isLongAbstract && !isExpanded
      ? `${pub.abstract!.substring(0, ABSTRACT_CHAR_LIMIT)}...`
      : pub.abstract;
      return (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <CardHeader>
        <CardTitle className="text-lg">
          {pub.publication_link ? (
            <a href={pub.publication_link} target="_blank" rel="noopener noreferrer" className="text-sky-700 hover:underline">
              {pub.title || 'No Title Available'}
            </a>
          ) : (
            <span className="text-slate-900">{pub.title || 'No Title Available'}</span>
          )}
        </CardTitle>
        <CardDescription>By {pub.authors?.join(', ') || 'N/A'}</CardDescription>
      </CardHeader>
      <CardContent>
        {/* The whitespace-pre-line class respects newlines in the abstract text */}
        <p className="text-sm text-slate-700 whitespace-pre-line">
          {abstractText || 'No abstract available.'}
        </p>
        {isLongAbstract && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-sm font-semibold text-sky-700 hover:underline mt-2"
          >
            {isExpanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </CardContent>
      <CardFooter className="flex flex-wrap justify-between items-center gap-4">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Badge variant="secondary">{pub.category || 'Unclassified'}</Badge>
          <Badge variant={getScoreBadgeVariant(pub.relevanceScore)}>
            Score: {pub.relevanceScore?.toFixed(3) || 'N/A'}
          </Badge>
        </div>
        <Button asChild size="sm" disabled={!pub.publication_link}>
          <a href={pub.publication_link || '#'} target="_blank" rel="noopener noreferrer">
            View Publication
            <ExternalLink className="ml-2 h-4 w-4" />
          </a>
        </Button>
      </CardFooter>
    </Card>
  );
};


const SearchEngine: React.FC = () => {
  const [query, setQuery] = useState<string>('');
  const [allPublications, setAllPublications] = useState<Publication[]>([]);
  const [, setTotalResults] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState<boolean>(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) {
      setError('Please enter a search query.');
      return;
    }

    setLoading(true);
    setError(null);
    setHasSearched(true);
    setCurrentPage(1);

    try {
      const data = await searchPublications({ query });
      setAllPublications(data.publications);
      setTotalResults(data.total);
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred.');
      setAllPublications([]);
      setTotalResults(0);
    } finally {
      setLoading(false);
    }
  };

  const paginatedPublications = useMemo(() => {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    return allPublications.slice(startIndex, startIndex + ITEMS_PER_PAGE);
  }, [allPublications, currentPage]);

  const totalPages = Math.ceil(allPublications.length / ITEMS_PER_PAGE);

  return (
    // --- UI IMPROVEMENT: Added a subtle background color to make cards stand out ---
    <div className="container mx-auto max-w-4xl p-4 sm:p-6 lg:p-8 bg-slate-50 min-h-screen">
      <header className="text-center mb-8">
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-900">Publication Search Engine</h1>
        <p className="text-slate-600 mt-2">Discover academic publications with ease.</p>
      </header>

      <form onSubmit={handleSearch} className="flex flex-col gap-4 mb-8">
        <div className="flex flex-col sm:flex-row gap-2">
          <Input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for publications..."
            className="flex-grow text-base text-black" // --- UI IMPROVEMENT: Slightly larger text ---
          />
          <Button type="submit" disabled={loading} className="w-full sm:w-auto">
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Search
          </Button>
        </div>
      </form>

      {error && <p className="text-destructive text-center mb-4">{error}</p>}

      {hasSearched && !loading && (
        <div className="flex justify-between items-center mb-6">
          <p className="text-sm text-slate-600">
            Showing <strong>{allPublications.length}</strong> results.
          </p>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center items-center py-12">
          <Loader2 className="h-10 w-10 animate-spin text-slate-400" />
        </div>
      ) : paginatedPublications.length > 0 ? (
        <div className="space-y-4">
          {paginatedPublications.map((pub, index) => (
            // --- MODIFIED: Using the new PublicationCard component ---
            <PublicationCard key={index} publication={pub} />
          ))}
        </div>
      ) : hasSearched && (
        <p className="text-center text-slate-500 py-12">No publications found for your query.</p>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 mt-8">
          <Button variant="outline" onClick={() => setCurrentPage(p => p - 1)} disabled={currentPage === 1}>
            Previous
          </Button>
          <span className="text-sm font-medium text-slate-700">Page {currentPage} of {totalPages}</span>
          <Button variant="outline" onClick={() => setCurrentPage(p => p + 1)} disabled={currentPage >= totalPages}>
            Next
          </Button>
        </div>
      )}
    </div>
  );
};

export default SearchEngine;