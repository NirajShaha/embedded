import { PageSelectionForm } from "@/components/page-selection-form";

type Params = { projectId: string; pageNumber: string };

export default async function SelectionStepPage({
  params,
}: {
  params: Promise<Params>;
}) {
  const { projectId, pageNumber } = await params;
  return (
    <PageSelectionForm
      projectId={Number(projectId)}
      pageNumber={Number(pageNumber)}
    />
  );
}