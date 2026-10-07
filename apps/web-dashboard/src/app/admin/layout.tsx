import AdminShell from "@/components/admin/AdminShell";

// Layout de toutes les routes /admin/... : il est separe du layout du
// dashboard restaurateur (/dashboard), qui garde sa propre Sidebar.
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <AdminShell>{children}</AdminShell>;
}
