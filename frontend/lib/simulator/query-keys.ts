export const simulatorKeys = {
  all: ["simulator"] as const,
  conversations: ["simulator", "conversations"] as const,
  messages: (donorId: string | null) =>
    ["simulator", "messages", donorId] as const,
  typing: (donorId: string | null) => ["simulator", "typing", donorId] as const,
};
