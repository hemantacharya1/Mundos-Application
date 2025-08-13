"use client"

import type React from "react"
import { Sidebar } from "@/components/sidebar"
import { useSidebar } from "@/components/sidebar-provider"

export function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const { isCollapsed } = useSidebar()

  return (
    <div className="h-screen bg-background overflow-hidden">
      <Sidebar />
      <main className={`h-full transition-all duration-300 ${isCollapsed ? "ml-16" : "ml-64"}`}>
        <div className="h-full">{children}</div>
      </main>
    </div>
  )
}
