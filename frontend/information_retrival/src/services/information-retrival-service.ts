import type { Publication } from "@/types/types";

const API_URL = "http://127.0.0.1:8000";

// Define a type for the classification result for better type safety
interface ClassificationResult {
    category: string;
    confidence: number;
}

export const searchPublications = async (query: string, page: number = 1, pageSize: number = 10): Promise<{ publications: Publication[], total: number }> => {
    try {
        const response = await fetch(`${API_URL}/api/search?page=${page}&page_size=${pageSize}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query }),
        });

        if (!response.ok) {
            throw new Error(`Backend API error: ${response.statusText}`);
        }

        const result = await response.json();
        return {
            publications: result.publications || [],
            total: result.total || 0
        };

    } catch (error) {
        console.error("Error searching publications via backend:", error);
        throw new Error("Failed to fetch publications from the backend.");
    }
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