import { JobPostingWithScore } from "./api";

// Global Singleton Memory Storage
// This will persist during SPA navigation (back/forward)
// but will be WIPED on page refresh (F5).
export interface MatchCache {
  userId: number | null;
  results: JobPostingWithScore[] | null;
}

export const matchCache: MatchCache = {
  userId: null,
  results: null,
};

export const clearMatchCache = () => {
  matchCache.userId = null;
  matchCache.results = null;
};
