import { Trans, useTranslation } from "react-i18next";

export function ParentPageState({ error }: { error: boolean }) {
  const { t } = useTranslation();
  if (error) {
    return (
      <div className="card mx-auto max-w-lg text-center">
        <p className="text-forest-700">{t("parent.states.error")}</p>
        <p className="mt-2 text-sm text-sage-600">{t("assessment.tryLater")}</p>
      </div>
    );
  }
  return (
    <div className="mx-auto max-w-6xl animate-pulse space-y-5" aria-busy="true">
      <div className="h-72 rounded-3xl bg-white" />
      <div className="grid gap-5 lg:grid-cols-2">
        <div className="h-56 rounded-2xl bg-white" />
        <div className="h-56 rounded-2xl bg-white" />
      </div>
    </div>
  );
}

export function NoChildConnected() {
  const { t } = useTranslation();
  return (
    <div className="card mx-auto max-w-xl md:p-10">
      <h1 className="text-3xl">{t("parent.states.noChild")}</h1>
      <p className="mt-3 leading-relaxed text-sage-600">
        <Trans i18nKey="parent.states.noChildText" components={{ code: <span className="font-medium text-forest-700" /> }} />
      </p>
    </div>
  );
}
