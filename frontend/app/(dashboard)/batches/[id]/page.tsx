import { BatchDetailScreen } from "@/components/features/batches/batch-detail-screen";

export default async function BatchDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<React.JSX.Element> {
  const { id } = await params;
  return <BatchDetailScreen batchId={id} />;
}
