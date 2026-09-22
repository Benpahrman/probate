import { useState, useEffect, useCallback } from 'react';
import { CaseItem } from '../types';
import { ApiService } from '../services/api';
import { uiStore } from '../stores/useUiStore';

export function useCases(countyId?: string) {
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCases = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await ApiService.getCases(countyId === 'ALL' ? undefined : countyId);
      setCases(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch cases');
    } finally {
      setLoading(false);
    }
  }, [countyId]);

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  const runScraper = async (fips: string, lookbackDays: number = 7) => {
    try {
      const res = await ApiService.triggerScraper(fips, lookbackDays);
      uiStore.addToast({
        type: 'success',
        title: 'Intake Completed',
        message: res.message || `Ingested cases for FIPS ${fips}`,
      });
      await fetchCases();
      return res;
    } catch (err: any) {
      uiStore.addToast({
        type: 'error',
        title: 'Scraper Error',
        message: err.message || 'Scraper execution failed',
      });
      return null;
    }
  };

  return { cases, loading, error, refetch: fetchCases, runScraper };
}
