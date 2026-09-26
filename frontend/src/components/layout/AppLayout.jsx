import { Outlet } from "react-router-dom";

import Sidebar from "./Sidebar";
import Header from "./Header";

export default function AppLayout() {
  return (
    <div className="min-h-screen bg-slate-100 flex">
      <Sidebar />

      <div className="flex-1 min-w-0">
        <Header />

        <main className="p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}