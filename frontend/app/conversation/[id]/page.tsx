import { LayoutWrapper } from "@/components/layout-wrapper"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Textarea } from "@/components/ui/textarea"
import { Separator } from "@/components/ui/separator"
import Link from "next/link"
import {
  ArrowLeft,
  Building2,
  Mail,
  Phone,
  Calendar,
  MessageSquare,
  Bot,
  User,
  Send,
  AlertTriangle,
  UserCheck,
  ArrowUp,
  Edit3,
} from "lucide-react"

export default function ConversationPage({ params }: { params: { id: string } }) {
  // Mock data - in real app, fetch based on params.id
  const lead = {
    id: params.id,
    name: "Sarah Johnson",
    company: "TechCorp Solutions",
    email: "sarah@techcorp.com",
    phone: "+1 (555) 123-4567",
    status: "Qualified",
    priority: "Critical",
    initialQuery: "Looking for enterprise CRM solution for 500+ employees with advanced analytics",
    attempts: 4,
    urgencyScore: 95,
    waitingTime: "8m 32s",
    handoffReason: "High-value prospect ready for immediate consultation",
    source: "Website",
    lastContact: "2 hours ago",
  }

  const conversation = [
    {
      id: 1,
      type: "ai",
      message:
        "Hello! I'm Morgan, your AI assistant. I understand you're looking for an enterprise CRM solution. Can you tell me more about your specific requirements?",
      timestamp: "2024-01-15 10:30 AM",
    },
    {
      id: 2,
      type: "user",
      message:
        "Hi Morgan! Yes, we're a growing company with about 500 employees and we need a comprehensive CRM that can handle our sales pipeline, customer analytics, and integrate with our existing tools.",
      timestamp: "2024-01-15 10:32 AM",
    },
    {
      id: 3,
      type: "ai",
      message:
        "That sounds like a substantial implementation! For a company of your size, you'll want enterprise-grade features. What's your current tech stack, and do you have any specific integration requirements?",
      timestamp: "2024-01-15 10:33 AM",
    },
    {
      id: 4,
      type: "user",
      message:
        "We're using Salesforce currently, but it's not meeting our analytics needs. We also use HubSpot for marketing, Slack for communication, and we have a custom billing system. The integration with our billing system is crucial.",
      timestamp: "2024-01-15 10:35 AM",
    },
    {
      id: 5,
      type: "ai",
      message:
        "I understand you need advanced analytics and custom billing integration. This sounds like a complex implementation that would benefit from our enterprise specialists. Let me connect you with one of our senior consultants who can provide a detailed assessment and custom pricing.",
      timestamp: "2024-01-15 10:37 AM",
    },
    {
      id: 6,
      type: "user",
      message:
        "That would be perfect! We're looking to implement this by Q4, so timing is important. Can someone reach out today?",
      timestamp: "2024-01-15 10:38 AM",
    },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Qualified":
        return "bg-green-500/10 text-green-500 border-green-500/20"
      case "In Progress":
        return "bg-blue-500/10 text-blue-500 border-blue-500/20"
      case "Urgent":
        return "bg-red-500/10 text-red-500 border-red-500/20"
      case "New":
        return "bg-purple-500/10 text-purple-500 border-purple-500/20"
      default:
        return "bg-gray-500/10 text-gray-500 border-gray-500/20"
    }
  }

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
      <div className="h-[calc(100vh-3rem)] flex flex-col">
        {/* Header - Fixed */}
        <div className="flex items-center gap-4 mb-4 flex-shrink-0">
          <Link href="/leads">
            <Button variant="ghost" size="sm" className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              Back to Leads
            </Button>
          </Link>
          <div className="flex-1">
            <h1 className="text-2xl font-bold">Conversation with {lead.name}</h1>
            <p className="text-sm text-muted-foreground">View and manage lead conversation history</p>
          </div>
        </div>

        {/* Main Content - Flexible */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-4 min-h-0">
          {/* Lead Information Sidebar - Compact */}
          <div className="lg:col-span-1 space-y-3 overflow-y-auto">
            {/* Lead Profile - Compact */}
            <Card className="glass-card">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <Avatar className="h-10 w-10">
                    <AvatarFallback className="bg-primary/10 text-primary text-sm">
                      {lead.name
                        .split(" ")
                        .map((n) => n[0])
                        .join("")}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-base truncate">{lead.name}</CardTitle>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Building2 className="h-3 w-3" />
                      <span className="truncate">{lead.company}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1 mt-2">
                  <Badge className={`${getStatusColor(lead.status)} text-xs px-2 py-0`}>{lead.status}</Badge>
                  <Badge className={`${getPriorityColor(lead.priority)} text-xs px-2 py-0`}>{lead.priority}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-2 pt-0">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs">
                    <Mail className="h-3 w-3 text-muted-foreground" />
                    <span className="truncate">{lead.email}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <Phone className="h-3 w-3 text-muted-foreground" />
                    <span>{lead.phone}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <Calendar className="h-3 w-3 text-muted-foreground" />
                    <span>Last: {lead.lastContact}</span>
                  </div>
                </div>

                <Separator />

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">Urgency</span>
                    <span className="text-xs font-bold text-red-500">{lead.urgencyScore}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">Attempts</span>
                    <span className="text-xs font-bold">{lead.attempts}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">Waiting</span>
                    <span className="text-xs font-bold text-blue-500">{lead.waitingTime}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Initial Query - Compact */}
            <Card className="glass-card">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <MessageSquare className="h-3 w-3 text-primary" />
                  Initial Query
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <p className="text-xs text-muted-foreground leading-relaxed">{lead.initialQuery}</p>
              </CardContent>
            </Card>

            {/* Handoff Reason - Compact */}
            {lead.handoffReason && (
              <Card className="glass-card">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <AlertTriangle className="h-3 w-3 text-orange-500" />
                    Handoff Reason
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-xs text-muted-foreground leading-relaxed">{lead.handoffReason}</p>
                </CardContent>
              </Card>
            )}

            {/* Actions - Compact */}
            <Card className="glass-card">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 pt-0">
                <Button size="sm" className="w-full gap-2 h-8">
                  <UserCheck className="h-3 w-3" />
                  Claim Lead
                </Button>
                <Button variant="outline" size="sm" className="w-full gap-2 bg-transparent h-8">
                  <ArrowUp className="h-3 w-3" />
                  Escalate
                </Button>
                <Button variant="outline" size="sm" className="w-full gap-2 bg-transparent h-8">
                  <Edit3 className="h-3 w-3" />
                  Edit Info
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Conversation - Fixed height with internal scrolling */}
          <div className="lg:col-span-3 min-h-0">
            <Card className="glass-card h-full flex flex-col">
              <CardHeader className="flex-shrink-0 pb-3">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <MessageSquare className="h-4 w-4" />
                  Conversation History
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col min-h-0 pt-0">
                {/* Messages - Scrollable */}
                <div className="flex-1 space-y-3 overflow-y-auto mb-3 pr-2 min-h-0">
                  {conversation.map((message) => (
                    <div key={message.id} className={`flex gap-2 ${message.type === "user" ? "flex-row-reverse" : ""}`}>
                      <Avatar className="h-7 w-7 flex-shrink-0">
                        <AvatarFallback
                          className={message.type === "ai" ? "bg-primary/10 text-primary" : "bg-accent/10 text-accent"}
                        >
                          {message.type === "ai" ? <Bot className="h-3 w-3" /> : <User className="h-3 w-3" />}
                        </AvatarFallback>
                      </Avatar>
                      <div className={`flex-1 max-w-[85%] ${message.type === "user" ? "text-right" : ""}`}>
                        <div
                          className={`p-3 rounded-lg ${
                            message.type === "ai"
                              ? "bg-muted/30 border border-border"
                              : "bg-primary/10 border border-primary/20"
                          }`}
                        >
                          <p className="text-sm leading-relaxed">{message.message}</p>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">{message.timestamp}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Message Input - Fixed */}
                <div className="border-t border-border pt-3 flex-shrink-0">
                  <div className="flex gap-2">
                    <Textarea
                      placeholder="Type your message..."
                      className="flex-1 min-h-[50px] max-h-[100px] resize-none text-sm"
                    />
                    <Button className="gap-2 self-end h-[50px]">
                      <Send className="h-4 w-4" />
                      Send
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </LayoutWrapper>
  )
}
