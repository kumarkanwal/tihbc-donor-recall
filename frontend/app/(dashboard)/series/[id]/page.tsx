import { SeriesEditorScreen } from "@/components/features/series/series-editor-screen";

export default async function SeriesEditorPage({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<React.JSX.Element> {
  const { id } = await params;
  return <SeriesEditorScreen seriesId={id} />;
}
