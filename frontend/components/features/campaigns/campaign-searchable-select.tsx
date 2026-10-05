import { Input } from "@/components/ui/input";

export interface CampaignSelectOption {
  value: string;
  label: string;
}

interface CampaignSearchableSelectProps {
  id: string;
  label: string;
  value: string;
  options: CampaignSelectOption[];
  disabled?: boolean;
  error?: string;
  onChange: (value: string) => void;
  onSearchChange: (value: string) => void;
}

/** Search input paired with a native, keyboard-friendly option selector. */
export function CampaignSearchableSelect({
  id,
  label,
  value,
  options,
  disabled = false,
  error,
  onChange,
  onSearchChange,
}: CampaignSearchableSelectProps): React.JSX.Element {
  return (
    <div>
      <label htmlFor={id} className="text-sm font-medium">
        {label}
      </label>
      <Input
        aria-label={`Search ${label.toLocaleLowerCase()}`}
        placeholder={`Search ${label.toLocaleLowerCase()}`}
        className="mt-2"
        disabled={disabled}
        onChange={(event) => onSearchChange(event.target.value)}
      />
      <select
        id={id}
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        className="border-border bg-surface rounded-control focus-visible:outline-ring mt-2 h-10 w-full border px-3 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 disabled:opacity-50"
      >
        <option value="">Select {label.toLocaleLowerCase()}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error ? <p className="text-danger mt-1 text-xs">{error}</p> : null}
    </div>
  );
}
