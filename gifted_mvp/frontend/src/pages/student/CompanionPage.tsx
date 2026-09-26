import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { companionApi } from "../../api/companion";
import { useAuth } from "../../features/auth/AuthContext";
import { CompanionHero } from "../../features/companion/CompanionHero";
import { AboutYouCard, PrivacyNotice, SuggestedPrompts } from "../../features/companion/CompanionSidebar";
import { DiaryMoments, DiaryOfferCard } from "../../features/companion/DiaryOffer";
import { ConversationPanel } from "../../features/companion/ConversationPanel";
import { useCompanionChat } from "../../features/companion/useCompanionChat";

/** /app/companion — the learner's private AI thinking partner. */
export function CompanionPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const chat = useCompanionChat();
  const overview = useQuery({ queryKey: ["companion-overview"], queryFn: companionApi.overview });
  const firstName =
    overview.data?.about.first_name || user?.full_name?.split(" ")[0] || t("dashboard.there");

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <CompanionHero />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <ConversationPanel
          firstName={firstName}
          messages={chat.messages}
          conversations={chat.conversations}
          activeId={chat.activeId}
          loading={chat.loading}
          loadError={chat.loadError}
          pending={chat.pending}
          sending={chat.sending}
          creating={chat.creating}
          onSend={chat.send}
          onRetry={chat.retry}
          onNewChat={chat.newChat}
          onOpen={chat.open}
          renderAssistantActions={(m) =>
            chat.activeId !== null && <DiaryOfferCard message={m} conversationId={chat.activeId} />
          }
        />

        <aside className="space-y-5">
          <AboutYouCard about={overview.data?.about} loading={overview.isLoading} />
          <SuggestedPrompts
            prompts={overview.data?.suggested_prompts ?? []}
            loading={overview.isLoading}
            disabled={chat.sending || chat.creating}
            onPick={(text) => void chat.send(text)}
          />
          <DiaryMoments />
          <PrivacyNotice />
        </aside>
      </div>
    </div>
  );
}
