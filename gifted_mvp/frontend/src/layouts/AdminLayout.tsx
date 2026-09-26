import { SidebarLayout, type NavItem } from "../components/SidebarLayout";

const items: NavItem[] = [{ to: "/admin", label: "nav.overview", end: true }];

export function AdminLayout() {
  return <SidebarLayout items={items} />;
}
