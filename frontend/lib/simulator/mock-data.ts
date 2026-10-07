import type {
  SimulatorConversation,
  SimulatorDonor,
  SimulatorMessage,
} from "./types";

export const MOCK_CAMPAIGNS = [
  { id: "campaign-regular", name: "October Regular Recall" },
  { id: "campaign-lapsed", name: "Lapsed Donor Win-back" },
] as const;

const donors: SimulatorDonor[] = [
  {
    id: "donor-aisha",
    name: "Aisha Khan",
    phone: "+923001234567",
    language: "en",
    sim_reachable: true,
    read_receipts: true,
    campaign_id: "campaign-regular",
    campaign_name: "October Regular Recall",
  },
  {
    id: "donor-hamza",
    name: "Hamza Ahmed",
    phone: "+923111112233",
    language: "en",
    sim_reachable: true,
    read_receipts: false,
    campaign_id: "campaign-lapsed",
    campaign_name: "Lapsed Donor Win-back",
  },
  {
    id: "donor-fatima",
    name: "فاطمہ علی",
    phone: "+923221234589",
    language: "ur",
    sim_reachable: true,
    read_receipts: true,
    campaign_id: "campaign-regular",
    campaign_name: "October Regular Recall",
  },
  {
    id: "donor-bilal",
    name: "Bilal Raza",
    phone: "+923331234500",
    language: "en",
    sim_reachable: false,
    read_receipts: false,
    campaign_id: "campaign-lapsed",
    campaign_name: "Lapsed Donor Win-back",
  },
];

const buttons = {
  en: [
    { id: "btn_confirm", label: "Confirm" },
    { id: "btn_reschedule", label: "Reschedule" },
    { id: "btn_decline", label: "Not now" },
  ],
  ur: [
    { id: "btn_confirm", label: "تصدیق کریں" },
    { id: "btn_reschedule", label: "دوسرا وقت" },
    { id: "btn_decline", label: "ابھی نہیں" },
  ],
} as const;

const recallText = {
  en: "Assalam-o-Alaikum Aisha Khan, thank you for being a regular blood donor with Team Indus Health & Blood Center. Your last donation helped patients who needed it most. You are now eligible to donate again. Would you like to visit us at Korangi Campus Blood Center on Tuesday, 6 October at 10:00 AM?",
  ur: "السلام علیکم فاطمہ علی، ٹیم انڈس ہیلتھ اینڈ بلڈ سینٹر کے باقاعدہ خون عطیہ کنندہ ہونے کا شکریہ۔ آپ کے پچھلے عطیے سے ضرورت مند مریضوں کی مدد ہوئی۔ اب آپ دوبارہ خون عطیہ کر سکتے ہیں۔ کیا آپ ۶ اکتوبر کو کورنگی کیمپس بلڈ سینٹر تشریف لا سکتے ہیں؟",
};

function initialMessage(donor: SimulatorDonor, body: string): SimulatorMessage {
  return {
    id: `message-${donor.id}-recall`,
    donor_id: donor.id,
    direction: "outbound",
    kind: "template",
    body,
    media_type: "video",
    media_url: "/images/IHHN-Logo-02-150x150.webp",
    buttons: [...buttons[donor.language]],
    button_id: null,
    reply_to_message_id: null,
    status: "delivered",
    scheduled_at: "2026-10-04T09:30:00Z",
    created_at: "2026-10-04T09:30:00Z",
    sent_at: "2026-10-04T09:30:01Z",
    delivered_at: "2026-10-04T09:30:02Z",
    read_at: null,
  };
}

/** Fresh mock state for a simulator source instance. */
export function createMockSeed(): {
  conversations: SimulatorConversation[];
  messages: Map<string, SimulatorMessage[]>;
} {
  const messages = new Map<string, SimulatorMessage[]>();
  for (const donor of donors) {
    messages.set(
      donor.id,
      donor.sim_reachable
        ? [initialMessage(donor, recallText[donor.language])]
        : [],
    );
  }

  return {
    conversations: donors.map((donor) => ({
      donor: { ...donor },
      last_message: messages.get(donor.id)?.at(-1) ?? {
        ...initialMessage(donor, "Number not on WhatsApp"),
        status: "failed",
      },
      unread_count: donor.sim_reachable ? 1 : 0,
    })),
    messages,
  };
}
