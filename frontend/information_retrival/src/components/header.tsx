import {Page} from "@/types/types.ts";
import React from 'react';
import {SearchIcon} from "@/components/icons/search-icon.tsx";
import {ClassifierIcon} from "@/components/icons/classifier-icon.tsx";

interface HeaderProps {
  currentPage: Page;
  setCurrentPage: (page: Page) => void;
}

const Header: React.FC<HeaderProps> = ({ currentPage, setCurrentPage }) => {
  const navItemClasses = "flex items-center space-x-2 px-4 py-2 rounded-md transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-indigo-500";
  const activeClasses = "bg-indigo-600 text-white shadow-md";
  const inactiveClasses = "bg-gray-700 text-gray-300 hover:bg-gray-600";

  return (
    <header className="bg-gray-800 shadow-lg sticky top-0 z-10">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8 py-4 flex flex-col sm:flex-row justify-between items-center">
        <div className="text-center sm:text-left mb-4 sm:mb-0">
            <h1 className="text-2xl font-bold text-white tracking-tight">Intelligent Information Retrieval</h1>
            <p className="text-sm text-gray-400">Assignment Solution for ST7071CEM</p>
        </div>
        <nav className="flex space-x-4">
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
