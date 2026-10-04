"use client";

import { SimulatorMessageBubble } from "@/components/simulator/message-bubble";
import { SimulatorPhoneFrame } from "@/components/simulator/phone-frame";
import { LanguageTabs } from "@/components/shared/language-tabs";
import {
  getContentSeriesErrorMessage,
  useSeriesPreview,
  type SeriesLanguage,
} from "@/hooks/use-content-series";

/** Server-rendered sample message in the shared simulator frame. */
export function SeriesPreviewPanel({
  seriesId,
  stepId,
  languages,
  language,
  onLanguageChange,
}: {
  seriesId: string;
  stepId: string | null;
  languages: SeriesLanguage[];
  language: SeriesLanguage;
  onLanguageChange: (language: SeriesLanguage) => void;
}): React.JSX.Element {
  const preview = useSeriesPreview(seriesId, stepId, language);
  const content = stepId ? (
    preview.isPending ? (
      <p className="text-sim-secondary mt-32 text-center text-xs">
        Rendering preview
      </p>
    ) : preview.error ? (
      <p
        className="text-danger bg-sim-incoming mt-24 rounded p-3 text-center text-xs"
        role="alert"
      >
        {getContentSeriesErrorMessage(
          preview.error,
          "The preview could not be rendered.",
        )}
      </p>
    ) : preview.data ? (
      <SimulatorMessageBubble
        body={preview.data.body}
        buttons={preview.data.buttons}
        mediaType={preview.data.media_type}
        mediaUrl={preview.data.media_url}
        language={language}
      />
    ) : null
  ) : (
    <p className="text-sim-secondary mt-32 text-center text-xs">
      Select a step to preview its message.
    </p>
  );
  return (
    <section className="space-y-3 xl:sticky xl:top-24">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Live preview</h2>
        <LanguageTabs
          languages={languages}
          value={language}
          onValueChange={onLanguageChange}
          english={null}
          urdu={null}
          className="[&_[role=tabpanel]]:hidden"
        />
      </div>
      <SimulatorPhoneFrame>
        <div className="bg-sim-date-chip text-sim-date-text mx-auto mb-4 w-fit rounded px-3 py-1 text-[0.65rem] shadow-sm">
          Today
        </div>
        {content}
      </SimulatorPhoneFrame>
    </section>
  );
}
