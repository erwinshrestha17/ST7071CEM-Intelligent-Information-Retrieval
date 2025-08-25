// document-classifier.tsx

import React, { useState } from 'react';
import { classifyDocument } from "@/services/information-retrival-service.ts";
import { ClassifierIcon } from "@/components/icons/classifier-icon.tsx";
// --- UI IMPROVEMENT: Using consistent components from a UI library ---
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";

const DocumentClassifier: React.FC = () => {
  const [text, setText] = useState<string>('');
  const [result, setResult] = useState<string | null>(null);
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
      const { category, confidence } = await classifyDocument(text);
      setResult(category);
      setClassificationConfidence(confidence);
    } catch (err) {
      setError('An error occurred during classification. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // --- UI IMPROVEMENT: New color function for light-themed result badges ---
  const getResultClasses = (category: string | null): string => {
    switch(category?.toLowerCase()) {
        case 'business':
            return 'bg-blue-100 text-blue-800 border-blue-200';
        case 'health':
            return 'bg-green-100 text-green-800 border-green-200';
        case 'politics':
            return 'bg-purple-100 text-purple-800 border-purple-200';
        default:
            return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  }

  return (
    // --- UI IMPROVEMENT: Added standard padding and a subtle background ---
    <div className="space-y-8 p-4 sm:p-6 lg:p-8 bg-slate-50 min-h-screen">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-sky-600">Document Classifier</h2>
        <p className="mt-2 text-lg text-slate-600">Classify text into Business, Health, or Politics categories.</p>
      </div>

      {/* --- UI IMPROVEMENT: Using a Card component for better structure --- */}
      <Card className="max-w-2xl mx-auto">
        <CardContent className="p-6 space-y-4">
          <Textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Enter or paste text here to classify..."
            className="w-full h-48 text-base"
            rows={8}
          />
          <Button
            onClick={handleClassify}
            disabled={isLoading || !text.trim()}
            className="w-full"
          >
            {isLoading ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : <ClassifierIcon className="mr-2 h-5 w-5" />}
            <span>Classify Text</span>
          </Button>
        </CardContent>
      </Card>

      <div className="mt-8 max-w-2xl mx-auto">
        {isLoading && (
          <div className="flex justify-center items-center flex-col text-center">
            <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
            <p className="mt-4 text-slate-500">Analyzing document...</p>
          </div>
        )}
        {error && <p className="text-center text-destructive bg-red-100 p-4 rounded-md">{error}</p>}
        {result && classificationConfidence !== null && (
          <Card className="text-center">
            <CardContent className="p-6 space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-slate-800 mb-2">Classification Result:</h3>
                <p className={`text-2xl font-bold py-3 px-5 rounded-lg inline-block border ${getResultClasses(result)}`}>
                  {result}
                </p>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-800 mb-2">Confidence Score:</h3>
                <p className={`text-2xl font-bold py-3 px-5 rounded-lg inline-block border ${getResultClasses(result)}`}>
                  {(classificationConfidence * 100).toFixed(2)}%
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default DocumentClassifier;