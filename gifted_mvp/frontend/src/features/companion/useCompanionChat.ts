import { useQuery, useQueryClient } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { companionApi } from "../../api/companion";
import type { Conversation, SendResult } from "../../types/companion";

/** A message the learner sent that has no stored reply yet. */
export interface PendingTurn {
  clientId: string;
  content: string;
  conversationId: number;
  status: "sending" | "failed";
}

export const conversationKey = (id: number) => ["companion-conversation", id] as const;
export const CONVERSATIONS_KEY = ["companion-conversations"] as const;

function newClientId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") return crypto.randomUUID();
  // Non-secure contexts (e.g. a LAN IP over http) have no randomUUID.
  return "10000000-1000-4000-8000-100000000000".replace(/[018]/g, (c) =>
    (Number(c) ^ (Math.random() * 16) >> (Number(c) / 4)).toString(16),
  );
}

function withTurn(old: Conversation | undefined, r: SendResult): Conversation {
  const messages = (old?.messages ?? []).filter(
    (m) => m.id !== r.user_message.id && m.id !== r.assistant_message.id,
  );
  return { ...r.conversation, messages: [...messages, r.user_message, r.assistant_message] };
}

/** Companion chat state. The active conversation lives in `?c=<id>` so a refresh reopens it;
 * without it the newest conversation is opened. Sends are idempotent per clientId (a retry
 * re-uses it), and only one send can be in flight at a time. */
export function useCompanionChat() {
  const qc = useQueryClient();
  const [params, setParams] = useSearchParams();
  const activeId = Number(params.get("c")) || null;
  const [pending, setPending] = useState<PendingTurn | null>(null);
  const [creating, setCreating] = useState(false);
  const inFlight = useRef(false);

  const list = useQuery({ queryKey: CONVERSATIONS_KEY, queryFn: companionApi.conversations });
  const conversation = useQuery({
    queryKey: conversationKey(activeId ?? 0),
    queryFn: () => companionApi.conversation(activeId!),
    enabled: activeId !== null,
    retry: (count, err) => !(isAxiosError(err) && err.response?.status === 404) && count < 1,
  });

  const open = useCallback(
    (id: number | null) => setParams(id ? { c: String(id) } : {}, { replace: true }),
    [setParams],
  );

  // No conversation in the URL → reopen the newest one (if any).
  useEffect(() => {
    if (activeId === null && list.data?.length) open(list.data[0].id);
  }, [activeId, list.data, open]);

  // A conversation that no longer exists (or isn't ours) → start from the empty state.
  useEffect(() => {
    if (isAxiosError(conversation.error) && conversation.error.response?.status === 404) open(null);
  }, [conversation.error, open]);

  const deliver = useCallback(
    async (turn: PendingTurn) => {
      setPending({ ...turn, status: "sending" });
      try {
        const result = await companionApi.send(turn.conversationId, turn.content, turn.clientId);
        qc.setQueryData<Conversation>(conversationKey(turn.conversationId), (old) => withTurn(old, result));
        setPending(null);
        void qc.invalidateQueries({ queryKey: CONVERSATIONS_KEY });
      } catch {
        // 503 (Companion unavailable) or a network error: nothing was stored server-side,
        // so the same clientId can be retried safely.
        setPending({ ...turn, status: "failed" });
      }
    },
    [qc],
  );

  const send = useCallback(
    async (text: string) => {
      const content = text.trim();
      if (!content || inFlight.current) return false;
      inFlight.current = true;
      try {
        let id = activeId;
        if (id === null) {
          const created = await companionApi.create();
          qc.setQueryData(conversationKey(created.id), created);
          id = created.id;
          open(id);
        }
        await deliver({ clientId: newClientId(), content, conversationId: id, status: "sending" });
        return true;
      } catch {
        return false;
      } finally {
        inFlight.current = false;
      }
    },
    [activeId, deliver, open, qc],
  );

  const retry = useCallback(async () => {
    if (!pending || pending.status !== "failed" || inFlight.current) return;
    inFlight.current = true;
    try {
      await deliver(pending);
    } finally {
      inFlight.current = false;
    }
  }, [deliver, pending]);

  const newChat = useCallback(async () => {
    if (inFlight.current) return;
    setCreating(true);
    try {
      const created = await companionApi.create();
      qc.setQueryData(conversationKey(created.id), created);
      setPending(null);
      open(created.id);
    } finally {
      setCreating(false);
    }
  }, [open, qc]);

  const visiblePending = pending && pending.conversationId === activeId ? pending : null;

  return {
    activeId,
    conversations: list.data ?? [],
    messages: activeId ? (conversation.data?.messages ?? []) : [],
    loading: (activeId !== null && conversation.isLoading) || (activeId === null && list.isLoading),
    loadError: conversation.isError && !(isAxiosError(conversation.error) && conversation.error.response?.status === 404),
    pending: visiblePending,
    sending: pending?.status === "sending",
    creating,
    send,
    retry,
    newChat,
    open,
  };
}
