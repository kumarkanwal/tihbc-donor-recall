import type { SimulatorDonor, SimulatorReply } from "./types";

const autoReplies = {
  en: {
    confirm:
      "Thank you, {{name}}. Your visit is confirmed for Tuesday, 6 October at 10:00 AM at Korangi Campus Blood Center. Please eat well and drink plenty of water before donating.",
    reschedule:
      "No problem. Here are the next available times. Please choose one, or type a day that suits you.",
    decline:
      "We understand, {{name}}. May we know the reason? This helps us contact you at a better time.",
    closing:
      "Thank you for letting us know. We will reach out again later. Take care.",
    coordinator:
      "Thank you. A coordinator from Team Indus will contact you shortly.",
  },
  ur: {
    confirm:
      "شکریہ {{name}}۔ آپ کی آمد ۶ اکتوبر کو کورنگی کیمپس بلڈ سینٹر پر کنفرم ہو گئی ہے۔ عطیہ سے پہلے اچھی طرح کھانا کھائیں اور زیادہ پانی پئیں۔",
    reschedule:
      "کوئی مسئلہ نہیں۔ یہ اگلے دستیاب اوقات ہیں۔ ان میں سے ایک منتخب کریں، یا اپنی سہولت کا دن لکھ کر بھیجیں۔",
    decline:
      "ہم سمجھتے ہیں {{name}}۔ کیا ہم وجہ جان سکتے ہیں؟ اس سے ہمیں بہتر وقت پر آپ سے رابطہ کرنے میں مدد ملے گی۔",
    closing:
      "بتانے کا شکریہ۔ ہم بعد میں دوبارہ رابطہ کریں گے۔ اپنا خیال رکھیں۔",
    coordinator: "شکریہ۔ ٹیم انڈس کا ایک کوآرڈینیٹر جلد آپ سے رابطہ کرے گا۔",
  },
} as const;

const slots = {
  en: ["Sat 10 Oct, 11:00 AM", "Sun 11 Oct, 2:00 PM", "Mon 12 Oct, 10:00 AM"],
  ur: [
    "ہفتہ ۱۰ اکتوبر، صبح ۱۱ بجے",
    "اتوار ۱۱ اکتوبر، دوپہر ۲ بجے",
    "پیر ۱۲ اکتوبر، صبح ۱۰ بجے",
  ],
} as const;

/** Resolve the documented automatic response for one mock donor reply. */
export function resolveMockAutomaticReply(
  donor: SimulatorDonor,
  reply: SimulatorReply,
): { body: string; buttons: { id: string; label: string }[] } {
  const copy = autoReplies[donor.language];
  const id = reply.type === "button" ? reply.button_id : "free_text";
  if (id === "btn_confirm") {
    return { body: copy.confirm.replace("{{name}}", donor.name), buttons: [] };
  }
  if (id === "btn_reschedule") {
    return {
      body: copy.reschedule,
      buttons: slots[donor.language].map((label, index) => ({
        id: `btn_slot_${index + 1}`,
        label,
      })),
    };
  }
  if (id === "btn_decline") {
    const labels =
      donor.language === "ur"
        ? ["سفر میں ہوں", "صحت کی وجہ", "کوئی اور وجہ"]
        : ["Travelling", "Health reason", "Other"];
    return {
      body: copy.decline.replace("{{name}}", donor.name),
      buttons: labels.map((label, index) => ({
        id: ["btn_reason_travelling", "btn_reason_health", "btn_reason_other"][
          index
        ],
        label,
      })),
    };
  }
  if (id.startsWith("btn_reason_")) {
    return { body: copy.closing, buttons: [] };
  }
  if (id.startsWith("btn_slot_")) {
    return { body: copy.confirm.replace("{{name}}", donor.name), buttons: [] };
  }
  return { body: copy.coordinator, buttons: [] };
}
