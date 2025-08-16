import './App.css'
import Header from "@/components/header.tsx";
import {Page} from "@/types/types.ts";
import SearchEngine from "@/components/search-engine.tsx";
import DocumentClassifier from "@/components/document-classifier.tsx";
import { useState } from "react";

function App() {
  const [currentPage, setCurrentPage] = useState<Page>(Page.SearchEngine);

  return (
  <div className="min-h-screen bg-gray-900 text-gray-100 font-sans">
      <Header currentPage={currentPage} setCurrentPage={setCurrentPage} />
      <main className="p-4 sm:p-6 md:p-8">
        <div className="max-w-4xl mx-auto">
          {currentPage === Page.SearchEngine && <SearchEngine />}
          {currentPage === Page.DocumentClassifier && <DocumentClassifier />}
        </div>
      </main>
      <footer className="text-center py-4 text-gray-500 text-sm">
        <p>Built for Module ST7071CEM: Intelligent Information Retrieval</p>
      </footer>
    </div>
  )
}

export default App
