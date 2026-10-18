import React from 'react';
import { useApp } from '../../context/AppContext';
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from 'lucide-react';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useApp();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 max-w-md w-full pointer-events-none">
      {toasts.map((toast) => {
        const iconConfig = {
          success: {
            icon: <CheckCircle2 className="w-4 h-4 text-[#80B89A] shrink-0" />,
            border: 'border-[#2D4536]',
            bg: 'bg-[#16211B]'
          },
          warning: {
            icon: <AlertTriangle className="w-4 h-4 text-[#D8B16C] shrink-0" />,
            border: 'border-[#4A3D22]',
            bg: 'bg-[#221D13]'
          },
          error: {
            icon: <AlertCircle className="w-4 h-4 text-[#D78383] shrink-0" />,
            border: 'border-[#4D2424]',
            bg: 'bg-[#241515]'
          },
          info: {
            icon: <Info className="w-4 h-4 text-[#91B7D8] shrink-0" />,
            border: 'border-[#243545]',
            bg: 'bg-[#151E26]'
          }
        }[toast.type];

        return (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-center justify-between gap-3 px-3.5 py-2.5 rounded border ${iconConfig.border} ${iconConfig.bg} shadow-lg text-[13px] text-[#F3F4F6] transition-all duration-200 animate-in fade-in slide-in-from-bottom-2`}
          >
            <div className="flex items-center gap-2.5 min-w-0">
              {iconConfig.icon}
              <span className="truncate">{toast.message}</span>
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="p-1 rounded text-[#727780] hover:text-[#F3F4F6] hover:bg-[#2A2E35] transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
};
