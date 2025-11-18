import { ExtractedProfile, CareerAdviceResponse, AdviceRequestData } from "../types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

const handleResponse = async (response: Response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
    throw new Error(errorData.detail || 'An unknown server error occurred.');
  }
  return response.json();
};

export const uploadCv = async (file: File): Promise<{ filename: string, text: string }> => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_URL}/cv/parse`, { 
    method: 'POST',
    body: formData,
  });
  return handleResponse(response);
};

export const extractProfile = async (cvText: string): Promise<{ profile: ExtractedProfile }> => {
  const response = await fetch(`${API_URL}/profile/extract`, { 
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cv_text: cvText }),
  });
  return handleResponse(response);
};

export const generateAdvice = async (data: AdviceRequestData): Promise<{ advice: CareerAdviceResponse }> => {
  const response = await fetch(`${API_URL}/advice/generate`, { 
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse(response);
};

export const validateRole = async (role: string): Promise<{ is_in_scope: boolean, reason: string }> => {
  const response = await fetch(`${API_URL}/role/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role }),
  });
  return handleResponse(response);
};