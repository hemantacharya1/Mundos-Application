"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { LayoutDashboard, Users, UserCheck, Menu, X, Sun, Moon, Calendar } from "lucide-react"
import { useTheme } from "next-themes"
import { useSidebar } from "@/components/sidebar-provider"

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "All Leads", href: "/leads", icon: Users },
  { name: "Handoff Queue", href: "/handoff", icon: UserCheck },
  { name: "Appointments", href: "/appointments", icon: Calendar },
]

export function Sidebar() {
  const { isCollapsed, toggleSidebar } = useSidebar()
  const pathname = usePathname()
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  // Prevent hydration mismatch by only rendering theme-dependent content after mount
  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <div
      className={cn(
        "fixed left-0 top-0 z-40 h-screen bg-card border-r border-border transition-all duration-300",
        isCollapsed ? "w-16" : "w-64",
      )}
    >
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-border">
          {!isCollapsed && (
            <h1 className="text-xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              AI Leads
            </h1>
          )}
          <Button variant="ghost" size="icon" onClick={toggleSidebar} className="h-8 w-8">
            {isCollapsed ? <Menu className="h-4 w-4" /> : <X className="h-4 w-4" />}
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-2 p-4">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link key={item.name} href={item.href}>
                <Button
                  variant={isActive ? "secondary" : "ghost"}
                  className={cn(
                    "w-full justify-start gap-3 h-12",
                    isCollapsed && "px-2",
                    isActive && "bg-primary/10 text-primary border border-primary/20",
                  )}
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" />
                  {!isCollapsed && <span>{item.name}</span>}
                </Button>
              </Link>
            )
          })}
        </nav>

        {/* Theme Toggle */}
        <div className="p-4 border-t border-border">
          <Button
            variant="ghost"
            size={isCollapsed ? "icon" : "default"}
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className={cn("w-full", isCollapsed ? "px-2" : "justify-start gap-3")}
          >
            {mounted ? (
              theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />
            ) : (
              <Sun className="h-5 w-5" />
            )}
            {!isCollapsed && <span>Toggle Theme</span>}
          </Button>
        </div>
      </div>
    </div>
  )
}
