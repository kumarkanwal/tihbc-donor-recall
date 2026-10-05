"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  simulatorSource,
  type ConversationFilters,
  type SimulatorReply,
} from "@/lib/simulator";
import { simulatorKeys } from "@/lib/simulator/query-keys";

const conversationKey = simulatorKeys.conversations;

/** Load donor conversations from the active simulator source. */
export function useSimulatorConversations(filters: ConversationFilters) {
  return useQuery({
    queryKey: [...conversationKey, filters],
    queryFn: () => simulatorSource.listConversations(filters),
  });
}

/** Load one donor chat and reconcile its live events. */
export function useSimulatorMessages(donorId: string | null) {
  const messagesKey = simulatorKeys.messages(donorId);
  const query = useQuery({
    queryKey: messagesKey,
    queryFn: () => simulatorSource.listMessages(donorId ?? ""),
    enabled: Boolean(donorId),
  });
  const typing = useQuery({
    queryKey: simulatorKeys.typing(donorId),
    queryFn: () => false,
    initialData: false,
    staleTime: Infinity,
    enabled: Boolean(donorId),
  });
  return { ...query, isTyping: typing.data };
}

/** Mark a conversation opened and refresh its read state. */
export function useOpenSimulatorConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (donorId: string) => simulatorSource.openConversation(donorId),
    onSuccess: (_result, donorId) => {
      void queryClient.invalidateQueries({
        queryKey: ["simulator", "messages", donorId],
      });
      void queryClient.invalidateQueries({ queryKey: conversationKey });
    },
  });
}

/** Send a donor reply through the active source. */
export function useSendSimulatorReply(donorId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (reply: SimulatorReply) =>
      simulatorSource.sendReply(donorId, reply),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["simulator", "messages", donorId],
      });
      void queryClient.invalidateQueries({ queryKey: conversationKey });
    },
  });
}
