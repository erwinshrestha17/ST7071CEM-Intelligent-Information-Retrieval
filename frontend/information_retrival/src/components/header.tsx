// header.tsx

import {Page} from "@/types/types.ts";
import React from 'react';
import {SearchIcon} from "@/components/icons/search-icon.tsx";
import {ClassifierIcon} from "@/components/icons/classifier-icon.tsx";

interface HeaderProps {
  currentPage: Page;
  setCurrentPage: (page: Page) => void;
}

const Header: React.FC<HeaderProps> = ({ currentPage, setCurrentPage }) => {
  // --- UI IMPROVEMENT: Updated classes for a light theme ---
  const navItemClasses = "flex items-center space-x-2 px-4 py-2 rounded-md transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500";
  const activeClasses = "bg-sky-600 text-white shadow-sm";
  const inactiveClasses = "text-slate-600 hover:bg-slate-100 hover:text-slate-900";

  return (
    // --- UI IMPROVEMENT: Light background with a bottom border ---
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8 py-4 flex flex-col sm:flex-row justify-between items-center">
        <div className="text-center sm:text-left mb-4 sm:mb-0">
            {/* --- UI IMPROVEMENT: Darker text for better contrast --- */}
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Intelligent Information Retrieval</h1>
            <p className="text-sm text-slate-500">Assignment Solution for ST7071CEM</p>
        </div>
        <nav className="flex space-x-2 sm:space-x-4">
          <button
            onClick={() => setCurrentPage(Page.SearchEngine)}
            className={`${navItemClasses} ${currentPage === Page.SearchEngine ? activeClasses : inactiveClasses}`}
          >
            <SearchIcon className="h-5 w-5" />
            <span>Search Engine</span>
          </button>
          <button
            onClick={() => setCurrentPage(Page.DocumentClassifier)}
            className={`${navItemClasses} ${currentPage === Page.DocumentClassifier ? activeClasses : inactiveClasses}`}
          >
            <ClassifierIcon className="h-5 w-5" />
            <span>Classifier</span>
          </button>
        </nav>
      </div>
    </header>
  );
};

export default Header;