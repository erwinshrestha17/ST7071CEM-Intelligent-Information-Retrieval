import './App.css'
import Header from "@/components/header.tsx";
import {Page} from "@/types/types.ts";
import SearchEngine from "@/components/search-engine.tsx";
import DocumentClassifier from "@/components/document-classifier.tsx";
import { useState } from "react";

function App() {
  const [currentPage, setCurrentPage] = useState<Page>(Page.SearchEngine);

  return (
<div className="min-h-screen bg-white text-slate-800 font-sans flex flex-col"> {/* <-- ADDED flex and flex-col */}
    <Header currentPage={currentPage} setCurrentPage={setCurrentPage} />
    {/* The main content area is now unstyled, allowing child components to control their own background */}
    <main className="flex-grow"> {/* <-- ADDED flex-grow */}
      <div>
        {currentPage === Page.SearchEngine && <SearchEngine />}
        {currentPage === Page.DocumentClassifier && <DocumentClassifier />}
      </div>
    </main>
    {/* --- UI IMPROVEMENT: Adjusted footer text color for light background --- */}
    <footer className="text-center py-4 text-slate-500 text-sm border-t border-slate-200">
      <p>Built for Module ST7071CEM: Intelligent Information Retrieval</p>
    </footer>
  </div>
  )
}

export default App
