import { useState, useEffect, useCallback } from 'react';
import { ExceptionItem } from '../types';
import { ApiService } from '../services/api';
import { uiStore } from '../stores/useUiStore';

export function useExceptions() {
  const [exceptions, setExceptions] = useState<ExceptionItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchExceptions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await ApiService.getExceptions();
      
      // Calculate dynamic SLA and urgency
      const enriched = data.map((exc) => {
        // High severity (> $200k equity) -> 4-hour SLA
        // Medium/Normal -> 24-hour SLA
        const isCritical = exc.severity === 'CRITICAL' || exc.type?.includes('GATE_1') || exc.type?.includes('GATE_4');
        const slaHours = isCritical ? 4 : 24;
        
        return {
          ...exc,
          severity: isCritical ? 'CRITICAL' : exc.severity || 'NORMAL',
          sla_hours_remaining: slaHours,
        };
      });

      setExceptions(enriched);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch exceptions');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchExceptions();
  }, [fetchExceptions]);

  const resolve = async (id: string, notes: string) => {
    try {
      await ApiService.resolveException(id, notes);
      uiStore.addToast({
        type: 'success',
        title: 'Exception Resolved',
        message: 'Corrective exception triage committed to audit trail.',
      });
      await fetchExceptions();
      return true;
    } catch (err: any) {
      uiStore.addToast({
        type: 'error',
        title: 'Resolution Failed',
        message: err.message || 'Failed to resolve exception',
      });
      return false;
    }
  };

  return { exceptions, loading, error, refetch: fetchExceptions, resolve };
}
