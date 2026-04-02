import { redirect } from "next/navigation";

export default function WorkspacePage() {
  return redirect("/workspace/chats/new");
}
