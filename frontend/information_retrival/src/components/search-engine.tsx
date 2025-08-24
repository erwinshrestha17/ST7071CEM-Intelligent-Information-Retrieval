
import React, { useState } from 'react';
import type {Publication} from "@/types/types.ts";
import {Spinner} from "@/components/spinner.tsx";
import {SearchIcon} from "lucide-react";
import {searchPublications} from "@/services/information-retrival-service.ts";
import {Button} from "@/components/ui/button.tsx";

const SearchEngine: React.FC = () => {
  const [query, setQuery] = useState<string>('');
  const [results, setResults] = useState<Publication[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState<boolean>(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);
    setHasSearched(true);
    setResults([]);

    try {
      const response = await searchPublications(query);
      setResults(response.publications);
    } catch (err) {
      setError('An error occurred while fetching search results. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h2 className="text-3xl font-extrabold text-indigo-400">Publication Search Engine</h2>
        <p className="mt-2 text-lg text-gray-400">Find publications from Coventry University's School of Economics, Finance and Accounting.</p>
      </div>

      <form onSubmit={handleSearch} className="flex items-center gap-2 bg-gray-800 p-2 rounded-lg shadow-md max-w-2xl mx-auto">
        <div className="relative flex-grow">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., 'financial risk management'"
            className="w-full bg-gray-700 text-white placeholder-gray-400 px-4 py-3 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-shadow"
          />
        </div>
        <button
          type="submit"
          disabled={isLoading}
          className="flex items-center justify-center bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-bold py-3 px-6 rounded-md transition-colors duration-200"
        >
          {isLoading ? <Spinner /> : <SearchIcon className="h-5 w-5" />}
          <span className="hidden sm:inline ml-2">Search</span>
        </button>
      </form>

      <div className="mt-8">
        {isLoading && (
          <div className="flex justify-center items-center flex-col text-center">
            <Spinner />
            <p className="mt-4 text-gray-400">Searching for publications...</p>
          </div>
        )}
        {error && <p className="text-center text-red-400 bg-red-900/30 p-4 rounded-md">{error}</p>}

        {!isLoading && hasSearched && results.length === 0 && !error && (
            <div className="text-center text-gray-500 py-10">
                <h3 className="text-xl font-semibold">No Results Found</h3>
                <p>Try searching for a different keyword.</p>
            </div>
        )}

        {results.length > 0 && (
          <div className="space-y-4">
            {results.map((pub, index) => (
              <div key={index} className="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-700 hover:border-indigo-500 transition-all duration-300">
                <h3 className="text-xl font-bold text-indigo-400">
                    <a href={pub.publication_link} target="_blank" rel="noopener noreferrer">
                    {pub.title}
                    </a>
                </h3>
                <p className="text-sm text-gray-400 mt-2">
                  <span className="font-semibold">Authors:</span> {pub.authors.join(', ')}
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  <span className="font-semibold">Year:</span> {pub.publicationYear}
                </p>
            <div className="mt-4 flex flex-wrap gap-2">
                  {/* Wrap the link in a Button component with the asChild prop */}
                  <Button asChild>
                      <a href={pub.publication_link} target="_blank" rel="noopener noreferrer">
                      View Publication
                    </a>
                  </Button>

                  {/* Do the same for the author profile link */}
                  {pub.authorProfileUrl && (
                    <Button asChild variant="outline" className="text-indigo-400 hover:text-indigo-300">
                      <a href={pub.authorProfileUrl} target="_blank" rel="noopener noreferrer">
                        View Author Profile
                      </a>
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchEngine;
