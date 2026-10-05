import { CampaignDetailScreen } from "@/components/features/campaigns/campaign-detail-screen";

export default async function CampaignDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<React.JSX.Element> {
  const { id } = await params;
  return <CampaignDetailScreen campaignId={id} />;
}
