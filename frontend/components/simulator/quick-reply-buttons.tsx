import type { SimulatorButton } from "@/lib/simulator";

interface QuickReplyButtonsProps {
  buttons: SimulatorButton[];
  disabled?: boolean;
  onReply?: (button: SimulatorButton) => void;
}

/** Localized, full-width quick replies beneath an incoming bubble. */
export function QuickReplyButtons({
  buttons,
  disabled = false,
  onReply,
}: QuickReplyButtonsProps): React.JSX.Element | null {
  if (buttons.length === 0) return null;
  return (
    <div className="border-sim-secondary/20 border-t">
      {buttons.map((button) => (
        <button
          key={button.id}
          type="button"
          className="text-sim-button border-sim-secondary/20 w-full border-b px-3 py-2 text-center text-xs font-medium last:border-b-0 disabled:cursor-not-allowed disabled:opacity-45"
          disabled={disabled}
          onClick={() => onReply?.(button)}
        >
          {button.label}
        </button>
      ))}
    </div>
  );
}
