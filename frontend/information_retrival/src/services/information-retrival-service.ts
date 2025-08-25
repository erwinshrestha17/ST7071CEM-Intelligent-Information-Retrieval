import type {SearchParams, SearchResponse} from "@/types/types.ts";

const API_URL = "http://127.0.0.1:8000";

// Define a type for the classification result for better type safety
interface ClassificationResult {
    category: string;
    confidence: number;
}

const API_BASE_URL = 'http://127.0.0.1:8000/api';


/**
 * Searches for publications using the backend API.
 * @param params - The search parameters including the query.
 * @returns A promise that resolves to the search response.
 * @throws An error if the API call fails.
 */
export const searchPublications = async (params: SearchParams): Promise<SearchResponse> => {
  const { query } = params;

  // URL no longer contains year parameters
  const fullUrl = `${API_BASE_URL}/search`;

  const response = await fetch(fullUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `HTTP error! Status: ${response.status}`);
  }

  return response.json();
};

export const classifyDocument = async (documentText: string): Promise<ClassificationResult> => {
    try {
        const response = await fetch(`${API_URL}/api/classify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: documentText }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Backend API error: ${response.statusText} - ${errorData.detail || ''}`);
        }

        const result = await response.json();

        // Access the correct keys from the backend response
        return {
            category: result.predicted_category || "Unknown",
            confidence: result.confidence_score || 0
        };

    } catch (error) {
        console.error("Error classifying document via backend:", error);
        throw new Error("Failed to classify document with the backend.");
    }
};