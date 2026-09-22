import { useState, useEffect, useCallback } from 'react';
import { OpportunitySummary, FullPOFDossier, QualityControlAuditSummary } from '../types';
import { ApiService } from '../services/api';
import { uiStore } from '../stores/useUiStore';

export function useOpportunities(countyId?: string, stage?: string) {
  const [opportunities, setOpportunities] = useState<OpportunitySummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOpportunities = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await ApiService.getOpportunities({
        county_id: countyId === 'ALL' ? undefined : countyId,
        stage: stage === 'ALL' ? undefined : stage,
      });
      setOpportunities(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load opportunities');
      uiStore.addToast({
        type: 'error',
        title: 'Pipeline Error',
        message: err.message || 'Failed to fetch pipeline opportunities',
      });
    } finally {
      setLoading(false);
    }
  }, [countyId, stage]);

  useEffect(() => {
    fetchOpportunities();
  }, [fetchOpportunities]);

  const auditQC = async (id: string): Promise<QualityControlAuditSummary | null> => {
    try {
      const result = await ApiService.auditQualityControl(id);
      await fetchOpportunities(); // Refresh state
      return result;
    } catch (err: any) {
      uiStore.addToast({
        type: 'error',
        title: 'QC Audit Failed',
        message: err.message || 'Error executing quality control audit',
      });
      return null;
    }
  };

  const advanceStage = async (id: string, targetStage: string, notes?: string) => {
    try {
      await ApiService.transitionFSM(id, targetStage, notes);
      uiStore.addToast({
        type: 'success',
        title: 'Stage Advanced',
        message: `Opportunity successfully transitioned to ${targetStage}`,
      });
      await fetchOpportunities();
      return true;
    } catch (err: any) {
      uiStore.addToast({
        type: 'error',
        title: 'Transition Denied',
        message: err.message || 'Illegal FSM transition',
      });
      return false;
    }
  };

  const deliverDeal = async (id: string, notes?: string) => {
    try {
      await ApiService.deliverOpportunity(id, notes);
      uiStore.addToast({
        type: 'success',
        title: 'Deal Delivered',
        message: 'Certified opportunity delivered to partner channel.',
      });
      await fetchOpportunities();
      return true;
    } catch (err: any) {
      uiStore.addToast({
        type: 'error',
        title: 'Delivery Failed',
        message: err.message || 'Cannot deliver uncertified opportunity',
      });
      return false;
    }
  };

  return {
    opportunities,
    loading,
    error,
    refetch: fetchOpportunities,
    auditQC,
    advanceStage,
    deliverDeal,
  };
}

export function useOpportunityWorkbench(id: string | null) {
  const [dossier, setDossier] = useState<FullPOFDossier | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDossier = useCallback(async () => {
    if (!id) {
      setDossier(null);
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const data = await ApiService.getOpportunityWorkbench(id);
      setDossier(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch dossier');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchDossier();
  }, [fetchDossier]);

  return { dossier, loading, error, refetch: fetchDossier };
}
