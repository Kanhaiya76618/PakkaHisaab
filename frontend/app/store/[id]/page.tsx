import { redirect } from "next/navigation";

export default function StorePage({ params }: { params: { id: string } }) { redirect(`/store/${params.id}/hisaab`); }
