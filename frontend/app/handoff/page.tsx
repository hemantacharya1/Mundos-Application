"use client"

import { LayoutWrapper } from "@/components/layout-wrapper"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import Link from "next/link"
import {
  AlertTriangle,
  Clock,
  Users,
  TrendingUp,
  Building2,
  MessageSquare,
  BarChart3,
  UserCheck,
  ArrowUp,
  Phone,
  Mail,
} from "lucide-react"

export default function HandoffPage() {
  const metrics = [
    {
      title: "Critical Leads",
      value: "12",
      icon: AlertTriangle,
      color: "text-red-500",
    },
    {
      title: "High Priority",
      value: "28",
      icon: TrendingUp,
      color: "text-orange-500",
    },
    {
      title: "Average Wait Time",
      value: "4.2m",
      icon: Clock,
      color: "text-blue-500",
    },
    {
      title: "Active Agents",
      value: "8",
      icon: Users,
      color: "text-green-500",
    },
  ]

  const handoffLeads = [
    {
      id: 1,
      name: "Sarah Johnson",
      company: "TechCorp Solutions",
      email: "sarah@techcorp.com",
      phone: "+1 (555) 123-4567",
      initialQuery: "Urgent enterprise CRM implementation needed for Q4 launch",
      handoffReason: "High-value prospect ready for immediate consultation",
      urgencyScore: 95,
      attempts: 4,
      waitingTime: "8m 32s",
      priority: "Critical",
    },
    {
      id: 2,
      name: "Michael Chen",
      company: "Innovate Labs",
      email: "m.chen@innovate.io",
      phone: "+1 (555) 987-6543",
      initialQuery: "Looking for AI analytics solution with custom integrations",
      handoffReason: "Technical requirements exceed AI capability",
      urgencyScore: 78,
      attempts: 3,
      waitingTime: "12m 15s",
      priority: "High",
    },
    {
      id: 3,
      name: "Emma Wilson",
      company: "StartupCo",
      email: "emma.w@startup.com",
      phone: "+1 (555) 456-7890",
      initialQuery: "Current system failing, need immediate replacement solution",
      handoffReason: "Critical timeline requires human intervention",
      urgencyScore: 92,
      attempts: 6,
      waitingTime: "15m 48s",
      priority: "Critical",
    },
    {
      id: 4,
      name: "Alex Rodriguez",
      company: "Global Dynamics",
      email: "alex@globaldyn.com",
      phone: "+1 (555) 234-5678",
      initialQuery: "Multi-location deployment with complex requirements",
      handoffReason: "Requires custom pricing and implementation planning",
      urgencyScore: 85,
      attempts: 2,
      waitingTime: "6m 22s",
      priority: "High",
    },
    {
      id: 5,
      name: "Lisa Park",
      company: "MedTech Inc",
      email: "lisa@medtech.com",
      phone: "+1 (555) 345-6789",
      initialQuery: "HIPAA-compliant solution needed urgently",
      handoffReason: "Compliance requirements need specialist review",
      urgencyScore: 88,
      attempts: 3,
      waitingTime: "9m 55s",
      priority: "Critical",
    },
  ]

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "Critical":
        return "bg-red-500/10 text-red-500 border-red-500/20"
      case "High":
        return "bg-orange-500/10 text-orange-500 border-orange-500/20"
      case "Medium":
        return "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"
      default:
        return "bg-gray-500/10 text-gray-500 border-gray-500/20"
    }
  }

  return (
    <LayoutWrapper>
      <div className="h-full flex flex-col">
        <div className="flex-shrink-0 space-y-4 p-6 border-b border-border/50">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Handoff Queue</h1>
              <p className="text-sm text-muted-foreground">Leads ready for human agent intervention</p>
            </div>
            <div className="flex items-center gap-2">
              <Select>
                <SelectTrigger className="w-32 h-8 text-xs">
                  <SelectValue placeholder="Urgency" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                </SelectContent>
              </Select>
              <Select>
                <SelectTrigger className="w-32 h-8 text-xs">
                  <SelectValue placeholder="Wait Time" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="under-5">Under 5 minutes</SelectItem>
                  <SelectItem value="over-15">Over 15 minutes</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-3">
            {metrics.map((metric, index) => (
              <Card key={index} className="glass-card">
                <CardContent className="p-3">
                  <div className="flex items-center gap-2">
                    <metric.icon className={`h-4 w-4 ${metric.color}`} />
                    <div>
                      <p className="text-xs text-muted-foreground">{metric.title}</p>
                      <p className="text-lg font-bold">{metric.value}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 pt-4">
          <div className="space-y-2">
            {handoffLeads.map((lead) => (
              <Link key={lead.id} href={`/conversation/${lead.id}`}>
                <Card
                  className={`glass-card hover:bg-card/70 transition-all duration-300 cursor-pointer ${
                    lead.priority === "Critical" ? "glow-border" : ""
                  }`}
                >
                  <CardContent className="p-3">
                    <div className="flex items-center gap-3">
                      <Avatar className="h-8 w-8 flex-shrink-0">
                        <AvatarFallback className="bg-primary/10 text-primary text-xs">
                          {lead.name
                            .split(" ")
                            .map((n) => n[0])
                            .join("")}
                        </AvatarFallback>
                      </Avatar>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-sm truncate">{lead.name}</h3>
                            <Badge className={`${getPriorityColor(lead.priority)} text-xs px-1.5 py-0`}>
                              {lead.priority}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-1">
                            <Button
                              size="sm"
                              className="gap-1 h-6 px-2 text-xs"
                              onClick={(e) => {
                                e.preventDefault()
                                e.stopPropagation()
                              }}
                            >
                              <UserCheck className="h-3 w-3" />
                              Claim
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              className="gap-1 h-6 px-2 text-xs bg-transparent"
                              onClick={(e) => {
                                e.preventDefault()
                                e.stopPropagation()
                              }}
                            >
                              <ArrowUp className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 text-xs text-muted-foreground mb-1">
                          <div className="flex items-center gap-1">
                            <Building2 className="h-3 w-3" />
                            <span className="truncate">{lead.company}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Mail className="h-3 w-3" />
                            <span className="truncate">{lead.email}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Phone className="h-3 w-3" />
                            <span>{lead.phone}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 mb-2 text-xs">
                          <div className="flex items-center gap-1 text-primary">
                            <MessageSquare className="h-3 w-3" />
                            <span className="truncate max-w-[200px]">{lead.initialQuery}</span>
                          </div>
                          <div className="text-muted-foreground">•</div>
                          <div className="flex items-center gap-1 text-orange-500">
                            <AlertTriangle className="h-3 w-3" />
                            <span className="truncate max-w-[200px]">{lead.handoffReason}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-4 text-xs">
                          <div className="flex items-center gap-1">
                            <TrendingUp className="h-3 w-3 text-red-500" />
                            <span className="font-medium">Score: {lead.urgencyScore}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <BarChart3 className="h-3 w-3 text-accent" />
                            <span className="font-medium">Attempts: {lead.attempts}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3 text-blue-500" />
                            <span className="font-medium">Waiting: {lead.waitingTime}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </LayoutWrapper>
  )
}
