import type {Publication} from "@/types/types"; // Make sure you have this type defined
const API_URL = "http://127.0.0.1:8000";


export const searchPublications = async (query: string): Promise<Publication[]> => {
    try {
        const response = await fetch(`${API_URL}/api/search`, {
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
        return result.publications || [];

    } catch (error) {
        console.error("Error searching publications via backend:", error);
        throw new Error("Failed to fetch publications from the backend.");
    }
};

export const classifyDocument = async (documentText: string): Promise<string> => {
    try {
        const response = await fetch(`${API_URL}/api/classify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: documentText }),
        });

        if (!response.ok) {
            throw new Error(`Backend API error: ${response.statusText}`);
        }

        const result = await response.json();
        return result.category || "";

    } catch (error) {
        console.error("Error classifying document via backend:", error);
        throw new Error("Failed to classify document with the backend.");
    }
};