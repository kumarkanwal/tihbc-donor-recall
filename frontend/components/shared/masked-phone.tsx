"use client";

import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";

interface MaskedPhoneProps {
  value: string;
  canReveal?: boolean;
}

function formatPakistaniPhone(value: string, masked: boolean): string {
  const digits = value.replace(/\D/g, "");
  if (digits.length === 12 && digits.startsWith("92")) {
    const prefix = `+${digits.slice(0, 2)} ${digits.slice(2, 5)}`;
    return masked
      ? `${prefix} *****${digits.slice(-2)}`
      : `${prefix} ${digits.slice(5)}`;
  }

  return masked
    ? `${"*".repeat(Math.max(0, value.length - 2))}${value.slice(-2)}`
    : value;
}

/** Mask a donor phone by default, with an explicitly permitted reveal. */
export function MaskedPhone({
  value,
  canReveal = false,
}: MaskedPhoneProps): React.JSX.Element {
  const [isRevealed, setIsRevealed] = useState(false);
  const displayedValue = formatPakistaniPhone(value, !isRevealed);

  return (
    <span className="inline-flex items-center gap-2 whitespace-nowrap">
      <span className="font-mono text-sm tabular-nums">{displayedValue}</span>
      {canReveal ? (
        <Button
          type="button"
          variant="ghost"
          size="small"
          onClick={() => setIsRevealed((current) => !current)}
          aria-label={isRevealed ? "Hide phone number" : "Reveal phone number"}
        >
          {isRevealed ? (
            <EyeOff aria-hidden="true" strokeWidth={1.75} />
          ) : (
            <Eye aria-hidden="true" strokeWidth={1.75} />
          )}
          {isRevealed ? "Hide" : "Reveal"}
        </Button>
      ) : null}
    </span>
  );
}
