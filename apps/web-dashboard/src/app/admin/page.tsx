import { redirect } from "next/navigation";

// /admin n'a pas de contenu propre : on renvoie vers la gestion des restaurants.
export default function AdminHome() {
  redirect("/admin/restaurants");
}
