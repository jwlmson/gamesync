import { X } from 'lucide-react';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export default function Modal({ open, onClose, title, children }: ModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-navy/50" onClick={onClose} />
      {/* Dialog */}
      <div className="card-hard relative z-10 w-full max-w-lg mx-4 p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-rokkitt text-lg font-bold uppercase tracking-wider">
            {title}
          </h3>
          <button onClick={onClose} className="p-1 hover:text-accent">
            <X className="w-5 h-5" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
