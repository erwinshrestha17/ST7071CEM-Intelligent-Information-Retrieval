import React, { useState } from 'react';
import { classifyDocument } from "@/services/information-retrival-service.ts";
import { ClassifierIcon } from "@/components/icons/classifier-icon.tsx";
import { Spinner } from "@/components/spinner.tsx";

const DocumentClassifier: React.FC = () => {
  const [text, setText] = useState<string>('');
  const [result, setResult] = useState<string | null>(null);
  // --- MODIFIED: Store confidence as a number for calculations ---
  const [classificationConfidence, setClassificationConfidence] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleClassify = async () => {
    if (!text.trim()) return;

    setIsLoading(true);
    setError(null);
    setResult(null);
    setClassificationConfidence(null);

    try {
      // --- MODIFIED: Destructure the object returned from the service ---
      const { category, confidence } = await classifyDocument(text);
      setResult(category);
      // Store the confidence score
      setClassificationConfidence(confidence);
    } catch (err) {
      setError('An error occurred during classification. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const getResultColor = (category: string | null) => {
    switch(category?.toLowerCase()) {
        case 'business':
            return 'bg-blue-900/50 text-blue-300 border-blue-500';
        case 'health':
            return 'bg-green-900/50 text-green-300 border-green-500';
        case 'politics':
            return 'bg-purple-900/50 text-purple-300 border-purple-500';
        default:
            return 'bg-gray-700 text-gray-300 border-gray-600';
    }
  }

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h2 className="text-3xl font-extrabold text-teal-400">Document Classifier</h2>
        <p className="mt-2 text-lg text-gray-400">Classify text into Business, Health, or Politics categories.</p>
      </div>

      <div className="bg-gray-800 p-4 rounded-lg shadow-md max-w-2xl mx-auto space-y-4">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter or paste text here to classify..."
          className="w-full h-48 bg-gray-700 text-white placeholder-gray-400 p-4 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 transition-shadow"
          rows={8}
        />
        <button
          onClick={handleClassify}
          disabled={isLoading}
          className="w-full flex items-center justify-center bg-teal-600 hover:bg-teal-700 disabled:bg-teal-400 text-white font-bold py-3 px-6 rounded-md transition-colors duration-200"
        >
          {isLoading ? <Spinner /> : <ClassifierIcon className="h-5 w-5" />}
          <span className="ml-2">Classify Text</span>
        </button>
      </div>

      <div className="mt-8 max-w-2xl mx-auto">
        {isLoading && (
          <div className="flex justify-center items-center flex-col text-center">
            <Spinner />
            <p className="mt-4 text-gray-400">Analyzing document...</p>
          </div>
        )}
        {error && <p className="text-center text-red-400 bg-red-900/30 p-4 rounded-md">{error}</p>}
        {result && classificationConfidence !== null && (
          <div className="text-center space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-300 mb-2">Classification Result:</h3>
              <p className={`text-2xl font-bold py-4 px-6 rounded-lg inline-block border ${getResultColor(result)}`}>
                {result}
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-300 mb-2">Confidence Score:</h3>
              {/* --- MODIFIED: Format the confidence score correctly as a percentage --- */}
              <p className={`text-2xl font-bold py-4 px-6 rounded-lg inline-block border ${getResultColor(result)}`}>
                {(classificationConfidence * 100).toFixed(2)}%
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentClassifier;