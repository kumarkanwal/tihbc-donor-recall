import { SeriesEditorScreen } from "@/components/features/series/series-editor-screen";

export default async function SeriesEditorPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ step?: string }>;
}): Promise<React.JSX.Element> {
  const { id } = await params;
  const { step } = await searchParams;
  return <SeriesEditorScreen seriesId={id} initialStepId={step} />;
}
