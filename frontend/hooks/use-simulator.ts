"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import {
  simulatorSource,
  type ConversationFilters,
  type SimulatorEvent,
  type SimulatorReply,
} from "@/lib/simulator";

const conversationKey = ["simulator", "conversations"] as const;

/** Load donor conversations from the active simulator source. */
export function useSimulatorConversations(filters: ConversationFilters) {
  return useQuery({
    queryKey: [...conversationKey, filters],
    queryFn: () => simulatorSource.listConversations(filters),
  });
}

/** Load one donor chat and reconcile its live events. */
export function useSimulatorMessages(donorId: string | null) {
  const queryClient = useQueryClient();
  const [isTyping, setIsTyping] = useState(false);
  const messagesKey = ["simulator", "messages", donorId] as const;
  const query = useQuery({
    queryKey: messagesKey,
    queryFn: () => simulatorSource.listMessages(donorId ?? ""),
    enabled: Boolean(donorId),
  });

  useEffect(() => {
    if (!donorId) return;
    return simulatorSource.subscribe((event: SimulatorEvent) => {
      const eventDonorId = event.payload.donor_id;
      if (eventDonorId !== donorId) return;
      if (event.type === "simulator.typing") {
        setIsTyping(event.payload.is_typing);
        return;
      }
      void queryClient.invalidateQueries({ queryKey: messagesKey });
      void queryClient.invalidateQueries({ queryKey: conversationKey });
    });
  }, [donorId, queryClient]);

  return { ...query, isTyping };
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
