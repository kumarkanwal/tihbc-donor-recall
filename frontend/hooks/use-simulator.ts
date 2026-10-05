"use client";

import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { env } from "@/lib/env";
import { useUiStore } from "@/lib/stores/ui-store";

import {
  simulatorSource,
  type ConversationFilters,
  type SimulatorReply,
} from "@/lib/simulator";
import { simulatorKeys } from "@/lib/simulator/query-keys";
import { simulatorPollInterval } from "@/lib/simulator/refresh-policy";
import {
  optimisticReply,
  updateReplyCache,
  type MessageHistory,
} from "@/lib/simulator/reply-cache";

const conversationKey = simulatorKeys.conversations;

/** Load donor conversations from the active simulator source. */
export function useSimulatorConversations(filters: ConversationFilters) {
  const isOpen = useUiStore((state) => state.isDonorPhoneOpen);
  return useQuery({
    queryKey: [...conversationKey, filters],
    queryFn: () => simulatorSource.listConversations(filters),
    enabled: isOpen,
    refetchInterval: simulatorPollInterval(
      "conversations",
      isOpen,
      env.NEXT_PUBLIC_SIMULATOR_SOURCE,
      env.NEXT_PUBLIC_REALTIME,
    ),
  });
}

/** Load one donor chat and reconcile its live events. */
export function useSimulatorMessages(donorId: string | null) {
  const isOpen = useUiStore((state) => state.isDonorPhoneOpen);
  const messagesKey = simulatorKeys.messages(donorId);
  const query = useInfiniteQuery({
    queryKey: messagesKey,
    queryFn: ({ pageParam }) =>
      simulatorSource.listMessagePage(donorId ?? "", pageParam),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (page) => page.next_before ?? undefined,
    enabled: isOpen && Boolean(donorId),
    refetchInterval: simulatorPollInterval(
      "messages",
      isOpen && Boolean(donorId),
      env.NEXT_PUBLIC_SIMULATOR_SOURCE,
      env.NEXT_PUBLIC_REALTIME,
    ),
  });
  const typing = useQuery({
    queryKey: simulatorKeys.typing(donorId),
    queryFn: () => false,
    initialData: false,
    staleTime: Infinity,
    enabled: Boolean(donorId),
  });
  const messages = query.data?.pages
    .slice()
    .reverse()
    .flatMap((page) => page.items);
  return { ...query, data: messages, isTyping: typing.data };
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
  const key = simulatorKeys.messages(donorId);
  return useMutation({
    mutationFn: (reply: SimulatorReply) =>
      simulatorSource.sendReply(donorId, reply),
    onMutate: async (reply) => {
      await queryClient.cancelQueries({ queryKey: key });
      const history = queryClient.getQueryData<MessageHistory>(key);
      const message = optimisticReply(donorId, reply, history);
      queryClient.setQueryData<MessageHistory>(
        key,
        updateReplyCache(history, message.id, message),
      );
      return message.id;
    },
    onError: (_error, _reply, optimisticId) => {
      if (optimisticId)
        queryClient.setQueryData<MessageHistory>(key, (history) =>
          updateReplyCache(history, optimisticId),
        );
    },
    onSuccess: (message, _reply, optimisticId) => {
      queryClient.setQueryData<MessageHistory>(key, (history) =>
        updateReplyCache(history, optimisticId ?? "", message),
      );
      void queryClient.invalidateQueries({
        queryKey: ["simulator", "messages", donorId],
      });
      void queryClient.invalidateQueries({ queryKey: conversationKey });
    },
  });
}
