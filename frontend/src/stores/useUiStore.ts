/**
 * Gieni OS - UI State Store
 * Manages active workspace tabs, filters, modals, and telemetry subscriptions
 */

import { useState, useEffect } from 'react';

export type WorkspaceTab = 'pipeline' | 'county' | 'exceptions' | 'investigator' | 'counties' | 'dealroom';

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
}

interface UiState {
  activeTab: WorkspaceTab;
  selectedOpportunityId: string | null;
  selectedCounty: string;
  stageFilter: string;
  searchQuery: string;
  toasts: ToastMessage[];
}

let state: UiState = {
  activeTab: 'pipeline',
  selectedOpportunityId: null,
  selectedCounty: 'ALL',
  stageFilter: 'ALL',
  searchQuery: '',
  toasts: [],
};

const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((listener) => listener());
}

export const uiStore = {
  getState: () => state,
  
  setActiveTab: (tab: WorkspaceTab) => {
    state = { ...state, activeTab: tab };
    notify();
  },

  setSelectedOpportunityId: (id: string | null) => {
    state = { ...state, selectedOpportunityId: id };
    notify();
  },

  setSelectedCounty: (county: string) => {
    state = { ...state, selectedCounty: county };
    notify();
  },

  setStageFilter: (stage: string) => {
    state = { ...state, stageFilter: stage };
    notify();
  },

  setSearchQuery: (query: string) => {
    state = { ...state, searchQuery: query };
    notify();
  },

  addToast: (toast: Omit<ToastMessage, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9);
    const newToast: ToastMessage = { ...toast, id };
    state = { ...state, toasts: [...state.toasts, newToast] };
    notify();

    setTimeout(() => {
      uiStore.removeToast(id);
    }, 5000);
  },

  removeToast: (id: string) => {
    state = { ...state, toasts: state.toasts.filter((t) => t.id !== id) };
    notify();
  },

  subscribe: (listener: () => void) => {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  },
};

export function useUiStore(): UiState {
  const [current, setCurrent] = useState<UiState>(uiStore.getState());

  useEffect(() => {
    return uiStore.subscribe(() => {
      setCurrent(uiStore.getState());
    });
  }, []);

  return current;
}
