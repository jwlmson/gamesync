interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
}

export default function Toggle({ checked, onChange, label, disabled }: ToggleProps) {
  return (
    <label className="flex items-center gap-3 cursor-pointer select-none">
      <div
        data-on={checked ? 'true' : 'false'}
        onClick={() => !disabled && onChange(!checked)}
        className={`w-12 h-6 rounded-full border-2 border-navy transition-colors relative ${
          checked ? 'bg-accent' : 'bg-gray-300'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
      >
        <div
          className={`absolute top-0.5 w-4 h-4 bg-cream border-2 border-navy rounded-full transition-transform ${
            checked ? 'translate-x-6' : 'translate-x-0.5'
          }`}
        />
      </div>
      {label && (
        <span className="font-archivo text-sm font-bold uppercase tracking-wider">
          {label}
        </span>
      )}
    </label>
  );
}
