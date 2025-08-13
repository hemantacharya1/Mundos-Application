"use client"

import { LayoutWrapper } from "@/components/layout-wrapper"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Textarea } from "@/components/ui/textarea"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
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
  RefreshCw,
  AlertCircle,
} from "lucide-react"
import { useConversation } from "@/hooks/use-conversation"
import { 
  formatLeadName, 
  formatCompanyName, 
  calculateUrgencyScore, 
  getStatusDisplayInfo, 
  getPriorityColor, 
  formatTimeAgo, 
  formatWaitingTime 
} from "@/lib/conversation-utils"
import { useState, use } from "react"
import { LoadingSpinner } from "@/components/ui/loading-spinner"

export default function ConversationPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { lead, communications, isLoading, error, sendMessage, refreshData } = useConversation(id);
  const [messageInput, setMessageInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  const handleSendMessage = async () => {
    if (!messageInput.trim() || isSending) return;
    
    setIsSending(true);
    try {
      await sendMessage(messageInput);
      setMessageInput("");
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleRefresh = async () => {
    await refreshData();
    setLastRefreshed(new Date());
  };

  if (isLoading) {
    return (
      <LayoutWrapper>
        <div className="h-[calc(100vh-3rem)] flex flex-col px-4 lg:px-6 pt-4 lg:pt-6 pb-2">
          <div className="flex items-center gap-4 mb-4 flex-shrink-0">
            <Link href="/leads">
              <Button variant="ghost" size="sm" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Leads
              </Button>
            </Link>
            <div className="flex-1">
              <Skeleton className="h-8 w-64 mb-2" />
              <Skeleton className="h-4 w-96" />
            </div>
          </div>
          
          <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-4 min-h-0">
            <div className="lg:col-span-1 space-y-3">
              <Card className="glass-card">
                <CardHeader className="pb-3">
                  <div className="flex items-center gap-2">
                    <Skeleton className="h-10 w-10 rounded-full" />
                    <div className="flex-1">
                      <Skeleton className="h-5 w-32 mb-2" />
                      <Skeleton className="h-3 w-24" />
                    </div>
                  </div>
                  <div className="flex gap-2 mt-2">
                    <Skeleton className="h-5 w-16" />
                    <Skeleton className="h-5 w-20" />
                  </div>
                </CardHeader>
                <CardContent className="space-y-2 pt-0">
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-full" />
                </CardContent>
              </Card>
            </div>
            
            <div className="lg:col-span-3">
              <Card className="glass-card h-full">
                <CardHeader>
                  <Skeleton className="h-6 w-48" />
                </CardHeader>
                <CardContent className="space-y-3">
                  {[...Array(6)].map((_, i) => (
                    <div key={i} className="flex gap-2">
                      <Skeleton className="h-7 w-7 rounded-full" />
                      <Skeleton className="h-20 w-3/4" />
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </LayoutWrapper>
    );
  }

  if (error || !lead) {
    return (
      <LayoutWrapper>
        <div className="h-[calc(100vh-3rem)] flex flex-col px-4 lg:px-6 pt-4 lg:pt-6 pb-2">
          <div className="flex items-center gap-4 mb-4 flex-shrink-0">
            <Link href="/leads">
              <Button variant="ghost" size="sm" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Leads
              </Button>
            </Link>
          </div>
          
          <div className="flex-1 flex items-center justify-center">
            <Card className="glass-card max-w-md">
              <CardContent className="pt-6 text-center">
                <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                <h2 className="text-xl font-semibold mb-2">Error Loading Conversation</h2>
                <p className="text-muted-foreground mb-4">
                  {error || "Failed to load lead information"}
                </p>
                <div className="space-y-2">
                  <Button onClick={refreshData} className="w-full gap-2">
                    <RefreshCw className="h-4 w-4" />
                    Try Again
                  </Button>
                  <Link href="/leads">
                    <Button variant="outline" className="w-full">
                      Back to Leads
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </LayoutWrapper>
    );
  }

  const statusInfo = getStatusDisplayInfo(lead.status);
  const urgencyScore = calculateUrgencyScore(lead);
  const waitingTime = formatWaitingTime(lead);

  return (
    <LayoutWrapper>
      <div className="h-[calc(100vh-3rem)] flex flex-col px-4 lg:px-6 pt-4 lg:pt-6 pb-2">
        {/* Header - Fixed */}
        <div className="flex items-center gap-4 mb-4 flex-shrink-0">
          <Link href="/leads">
            <Button variant="ghost" size="sm" className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              Back to Leads
            </Button>
          </Link>
          <div className="flex-1">
            <h1 className="text-2xl font-bold">Conversation with {formatLeadName(lead)}</h1>
            <p className="text-sm text-muted-foreground">View and manage lead conversation history</p>
          </div>
          <Button variant="outline" size="sm" onClick={handleRefresh} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
          <div className="text-xs text-muted-foreground">
            Last updated: {formatTimeAgo(lastRefreshed.toISOString())}
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
                      {formatLeadName(lead)
                        .split(" ")
                        .map((n) => n[0])
                        .join("")}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-base truncate">{formatLeadName(lead)}</CardTitle>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Building2 className="h-3 w-3" />
                      <span className="truncate">{formatCompanyName(lead)}</span>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                      <span>Source: {lead.inquiry_date ? 'Website Form' : 'Manual Entry'}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1 mt-2">
                  <Badge className={`${statusInfo.color} text-xs px-2 py-0`}>{statusInfo.label}</Badge>
                  <Badge className={`${getPriorityColor(statusInfo.priority)} text-xs px-2 py-0`}>{statusInfo.priority}</Badge>
                </div>
                <div className="mt-2">
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <span>Status: {lead.status.replace(/_/g, ' ')}</span>
                    {lead.status === 'needs_immediate_attention' && (
                      <span className="text-red-500">⚠️</span>
                    )}
                    {lead.status === 'converted' && (
                      <span className="text-green-500">🎉</span>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-2 pt-0">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs">
                    <Mail className="h-3 w-3 text-muted-foreground" />
                    <span className="truncate">{lead.email}</span>
                  </div>
                  {lead.phone_number && (
                    <div className="flex items-center gap-2 text-xs">
                      <Phone className="h-3 w-3 text-muted-foreground" />
                      <span>{lead.phone_number}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-2 text-xs">
                    <Calendar className="h-3 w-3 text-muted-foreground" />
                    <span>Last: {formatTimeAgo(lead.updated_at)}</span>
                  </div>
                  {lead.created_at && (
                    <div className="flex items-center gap-2 text-xs">
                      <Calendar className="h-3 w-3 text-muted-foreground" />
                      <span>Created: {formatTimeAgo(lead.created_at)}</span>
                    </div>
                  )}
                  {lead.inquiry_date && lead.inquiry_date !== lead.created_at && (
                    <div className="flex items-center gap-2 text-xs">
                      <Calendar className="h-3 w-3 text-muted-foreground" />
                      <span>Inquiry: {formatTimeAgo(lead.inquiry_date)}</span>
                    </div>
                  )}
                </div>

                <Separator />

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">Urgency</span>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-bold ${
                        urgencyScore >= 80 ? 'text-red-500' : 
                        urgencyScore >= 60 ? 'text-orange-500' : 
                        urgencyScore >= 40 ? 'text-yellow-500' : 'text-green-500'
                      }`}>
                        {urgencyScore}
                      </span>
                      {urgencyScore >= 80 && (
                        <span className="text-xs text-red-500">🔥</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">Quality</span>
                    <span className={`text-xs font-bold ${
                      (lead.inquiry_notes?.length || 0) > 100 ? 'text-green-500' : 
                      (lead.inquiry_notes?.length || 0) > 50 ? 'text-yellow-500' : 'text-red-500'
                    }`}>
                      {lead.inquiry_notes ? (lead.inquiry_notes.length > 100 ? 'High' : lead.inquiry_notes.length > 50 ? 'Medium' : 'Low') : 'Unknown'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">Attempts</span>
                    <span className={`text-xs font-bold ${
                      lead.nurture_attempts > 3 ? 'text-red-500' : 
                      lead.nurture_attempts > 1 ? 'text-orange-500' : 'text-green-500'
                    }`}>
                      {lead.nurture_attempts}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">Waiting</span>
                    <span className={`text-xs font-bold ${
                      waitingTime.includes('d') ? 'text-red-500' : 
                      waitingTime.includes('h') && parseInt(waitingTime) > 2 ? 'text-orange-500' : 'text-blue-500'
                    }`}>
                      {waitingTime}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Initial Query - Compact */}
            {lead.inquiry_notes && (
              <Card className="glass-card">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <MessageSquare className="h-3 w-3 text-primary" />
                    Initial Query
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-xs text-muted-foreground leading-relaxed">{lead.inquiry_notes}</p>
                </CardContent>
              </Card>
            )}

            {/* AI Summary - Compact */}
            {lead.ai_summary && (
              <Card className="glass-card">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Bot className="h-3 w-3 text-primary" />
                    AI Summary
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-xs text-muted-foreground leading-relaxed">{lead.ai_summary}</p>
                </CardContent>
              </Card>
            )}

            {/* AI Drafted Reply - Compact */}
            {lead.ai_drafted_reply && (
              <Card className="glass-card">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Bot className="h-3 w-3 text-green-500" />
                    AI Drafted Reply
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-xs text-muted-foreground leading-relaxed mb-2">{lead.ai_drafted_reply}</p>
                  <Button size="sm" variant="outline" className="w-full h-6 text-xs">
                    Use This Reply
                  </Button>
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
                  {communications.length > 0 && (
                    <Badge variant="secondary" className="ml-2">
                      {communications.length} messages
                    </Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col min-h-0 pt-0">
                {/* Messages - Scrollable */}
                <div className="flex-1 space-y-3 overflow-y-auto mb-2 pr-2 min-h-0">
                  {communications.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p className="font-medium mb-2">No conversation history yet</p>
                      <p className="text-sm">Start the conversation by sending a message below</p>
                      <div className="mt-4 p-3 bg-muted/30 rounded-lg border border-dashed border-border">
                        <p className="text-xs text-muted-foreground">
                          💡 Tip: You can send emails, notes, or initiate AI calls from this interface
                        </p>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="text-center py-2">
                        <Badge variant="outline" className="text-xs">
                          {communications.length} message{communications.length !== 1 ? 's' : ''} in conversation
                        </Badge>
                        {communications.length > 0 && (
                          <div className="mt-2">
                            <Badge variant="secondary" className="text-xs mr-2">
                              {communications.filter(c => c.direction === 'incoming').length} incoming
                            </Badge>
                            <Badge variant="secondary" className="text-xs mr-2">
                              {communications.filter(c => c.direction === 'outgoing_manual').length} manual
                            </Badge>
                            <Badge variant="secondary" className="text-xs">
                              {communications.filter(c => c.direction === 'outgoing_auto').length} AI
                            </Badge>
                          </div>
                        )}
                      </div>
                      {communications.map((message) => (
                        <div key={message.id} className={`flex gap-2 ${message.direction === 'incoming' ? "flex-row-reverse" : ""}`}>
                          <Avatar className="h-7 w-7 flex-shrink-0">
                            <AvatarFallback
                              className={message.direction === 'incoming' ? "bg-accent/10 text-accent" : "bg-primary/10 text-primary"}
                            >
                              {message.direction === 'incoming' ? <User className="h-3 w-3" /> : <Bot className="h-3 w-3" />}
                            </AvatarFallback>
                          </Avatar>
                          <div className={`flex-1 max-w-[85%] ${message.direction === 'incoming' ? "text-right" : ""}`}>
                            <div
                              className={`p-3 rounded-lg ${
                                message.direction === 'incoming'
                                  ? "bg-primary/10 border border-primary/20"
                                  : "bg-muted/30 border border-border"
                              }`}
                            >
                              <p className="text-sm leading-relaxed">{message.content}</p>
                            </div>
                            <div className={`flex items-center gap-2 mt-1 ${message.direction === 'incoming' ? "justify-end" : ""}`}>
                              <p className="text-xs text-muted-foreground">{formatTimeAgo(message.sent_at)}</p>
                              <Badge variant="outline" className="text-xs px-1 py-0 h-4">
                                {message.type}
                              </Badge>
                              {message.direction === 'outgoing_auto' && (
                                <Badge variant="secondary" className="text-xs px-1 py-0 h-4">
                                  AI
                                </Badge>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </>
                  )}
                </div>

                {/* Message Input - Fixed */}
                <div className="border-t border-border pt-3 flex-shrink-0">
                  <div className="flex gap-2">
                    <Textarea
                      placeholder="Type your message..."
                      className="flex-1 min-h-[50px] max-h-[100px] resize-none text-sm"
                      value={messageInput}
                      onChange={(e) => setMessageInput(e.target.value)}
                      onKeyPress={handleKeyPress}
                      disabled={isSending}
                    />
                    <Button 
                      className="gap-2 self-end h-[50px]" 
                      onClick={handleSendMessage}
                      disabled={!messageInput.trim() || isSending}
                    >
                      {isSending ? (
                        <LoadingSpinner size="sm" className="text-white" />
                      ) : (
                        <Send className="h-4 w-4" />
                      )}
                      {isSending ? "Sending..." : "Send"}
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
