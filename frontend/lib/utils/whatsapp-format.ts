export interface WhatsAppFormatToken {
  kind: "text" | "bold" | "italic";
  value: string;
}

const FORMATTING_PATTERN = /(\*[^*\n]+\*|_[^_\n]+_)/g;
const LTR_RUN_PATTERN = /([A-Za-z0-9](?:[A-Za-z0-9 .,:/'&()+-]*[A-Za-z0-9])?)/g;

export interface BidiTextSegment {
  isolate: boolean;
  value: string;
}

/** Parse the small bold/italic formatting subset supported by WhatsApp. */
export function parseWhatsAppFormat(input: string): WhatsAppFormatToken[] {
  return input
    .split(FORMATTING_PATTERN)
    .filter(Boolean)
    .map((part) => {
      if (part.startsWith("*") && part.endsWith("*")) {
        return { kind: "bold", value: part.slice(1, -1) };
      }
      if (part.startsWith("_") && part.endsWith("_")) {
        return { kind: "italic", value: part.slice(1, -1) };
      }
      return { kind: "text", value: part };
    });
}

/** Identify Latin/numeric runs that need isolation inside an Urdu paragraph. */
export function splitBidiText(input: string): BidiTextSegment[] {
  return input
    .split(LTR_RUN_PATTERN)
    .filter(Boolean)
    .map((value) => ({ isolate: /[A-Za-z0-9]/.test(value), value }));
}
