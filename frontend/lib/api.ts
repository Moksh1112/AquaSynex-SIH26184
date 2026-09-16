const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchApi(endpoint: string, token?: string | null, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Set default Content-Type if it's not a FormData (which sets its own boundary) and not already set
  if (!(options.body instanceof URLSearchParams) && !(options.body instanceof FormData) && !headers['Content-Type']) {
     headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMsg = `Server error: ${response.status}`;
    try {
      const errorData = await response.json();
      errorMsg = errorData.detail || errorMsg;
    } catch (e) {
      // Ignore JSON parse error for error responses
    }
    const error = new Error(errorMsg);
    (error as any).status = response.status;
    throw error;
  }

// Handle empty responses
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

export interface ResponseIntelligence {
  nearest_station_id: string | null;
  nearest_station_name: string | null;
  station_latitude: number | null;
  station_longitude: number | null;
  distance_km: number | null;
  jurisdiction: string | null;
  recommended_action: string;
}

export interface EnrichedPredictionItem {
  rank: number;
  atm_id: string;
  probability: number;
  latitude: number;
  longitude: number;
  risk: string;
  response: ResponseIntelligence;
}
