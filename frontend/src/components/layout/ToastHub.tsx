import React from 'react';
import { useUiStore, uiStore, ToastMessage } from '../../stores/useUiStore';

const TOAST_TYPE_CLASSES: Record<ToastMessage['type'], string> = {
  error: 'bg-rose-950/90 border-rose-800 text-rose-200',
  success: 'bg-emerald-950/90 border-emerald-800 text-emerald-200',
  warning: 'bg-amber-950/90 border-amber-800 text-amber-200',
  info: 'bg-slate-900/90 border-slate-700 text-slate-200',
};

export const ToastHub: React.FC = () => {
  const { toasts } = useUiStore();

  if (!toasts.length) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2 max-w-sm pointer-events-none">
      {toasts.map((toast: ToastMessage) => {
        const colorClass = TOAST_TYPE_CLASSES[toast.type] || TOAST_TYPE_CLASSES.info;
        return (
          <div
            key={toast.id}
            className={`p-3.5 rounded-xl border shadow-xl backdrop-blur-md pointer-events-auto transition-all duration-300 ${colorClass}`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold font-mono uppercase">{toast.title}</span>
              <button
                onClick={() => uiStore.removeToast(toast.id)}
                className="text-xs opacity-60 hover:opacity-100 ml-2"
              >
                ✕
              </button>
            </div>
            <p className="text-xs mt-1 font-sans">{toast.message}</p>
          </div>
        );
      })}
    </div>
  );
};
