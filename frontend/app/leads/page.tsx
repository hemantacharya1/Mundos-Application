"use client"

import type React from "react"

import { LayoutWrapper } from "@/components/layout-wrapper"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import Link from "next/link"
import { Search, Plus, Mail, Phone, Building2, MessageSquare, BarChart3, Clock, Upload, FileText } from "lucide-react"
import { useState } from "react"

export default function LeadsPage() {
  const [isAddLeadOpen, setIsAddLeadOpen] = useState(false)
  const [isImportOpen, setIsImportOpen] = useState(false)
  const [dragActive, setDragActive] = useState(false)

  const leads = [
    {
      id: 1,
      name: "Sarah Johnson",
      email: "sarah@techcorp.com",
      phone: "+1 (555) 123-4567",
      company: "TechCorp Solutions",
      status: "Qualified",
      source: "Website",
      initialQuery: "Looking for enterprise CRM solution for 500+ employees",
      attempts: 3,
      lastContact: "2 hours ago",
    },
    {
      id: 2,
      name: "Michael Chen",
      email: "m.chen@innovate.io",
      phone: "+1 (555) 987-6543",
      company: "Innovate Labs",
      status: "In Progress",
      source: "Social Media",
      initialQuery: "Need AI-powered analytics for customer behavior tracking",
      attempts: 2,
      lastContact: "1 day ago",
    },
    {
      id: 3,
      name: "Emma Wilson",
      email: "emma.w@startup.com",
      phone: "+1 (555) 456-7890",
      company: "StartupCo",
      status: "Urgent",
      source: "Email Campaign",
      initialQuery: "Urgent: Current system failing, need immediate replacement",
      attempts: 5,
      lastContact: "30 minutes ago",
    },
    {
      id: 4,
      name: "David Park",
      email: "david@enterprise.net",
      phone: "+1 (555) 321-0987",
      company: "Enterprise Networks",
      status: "New",
      source: "Referral",
      initialQuery: "Interested in demo for team collaboration tools",
      attempts: 1,
      lastContact: "3 hours ago",
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

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    // Handle file drop logic here
  }

  const handleFileAreaClick = () => {
    const fileInput = document.getElementById("csv-upload") as HTMLInputElement
    if (fileInput) {
      fileInput.click()
    }
  }

  return (
    <LayoutWrapper>
      <div className="h-full flex flex-col">
        <div className="flex-shrink-0 p-6 border-b border-border/50">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold">All Leads</h1>
              <p className="text-sm text-muted-foreground">Manage and track all your leads in one place</p>
            </div>
            <div className="flex gap-3">
              <Dialog open={isImportOpen} onOpenChange={setIsImportOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="gap-2 bg-transparent">
                    <Upload className="h-4 w-4" />
                    Import Leads
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader>
                    <DialogTitle>Import Leads from CSV</DialogTitle>
                    <DialogDescription>
                      Upload a CSV file with your leads. Make sure your file includes columns for name, email, phone,
                      and initial query.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div
                      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
                        dragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
                      }`}
                      onDragEnter={handleDrag}
                      onDragLeave={handleDrag}
                      onDragOver={handleDrag}
                      onDrop={handleDrop}
                      onClick={handleFileAreaClick}
                    >
                      <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                      <div className="space-y-2">
                        <p className="text-sm font-medium">Drop your CSV file here</p>
                        <p className="text-xs text-muted-foreground">or click to browse</p>
                      </div>
                      <Input type="file" accept=".csv" className="hidden" id="csv-upload" />
                    </div>
                    <div className="text-xs text-muted-foreground space-y-1">
                      <p className="font-medium">Required columns:</p>
                      <p>• name, email, phone, initial_query</p>
                      <p>• Optional: company, source</p>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsImportOpen(false)}>
                      Cancel
                    </Button>
                    <Button>Upload CSV</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              <Dialog open={isAddLeadOpen} onOpenChange={setIsAddLeadOpen}>
                <DialogTrigger asChild>
                  <Button className="gap-2">
                    <Plus className="h-4 w-4" />
                    Add Lead
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader>
                    <DialogTitle>Add New Lead</DialogTitle>
                    <DialogDescription>Enter the lead information to add them to your pipeline.</DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">Full Name *</Label>
                      <Input id="name" placeholder="Enter full name" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email Address *</Label>
                      <Input id="email" type="email" placeholder="Enter email address" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="phone">Phone Number *</Label>
                      <Input id="phone" type="tel" placeholder="Enter phone number" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="company">Company (Optional)</Label>
                      <Input id="company" placeholder="Enter company name" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="query">Initial Query *</Label>
                      <Textarea
                        id="query"
                        placeholder="What is the lead interested in or asking about?"
                        className="min-h-[80px]"
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsAddLeadOpen(false)}>
                      Cancel
                    </Button>
                    <Button>Add Lead</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
          </div>

          {/* Inline Filters */}
          <div className="flex flex-wrap items-center gap-4">
            <div className="relative flex-1 min-w-[250px]">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Search leads..." className="pl-10" />
            </div>
            <Select>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="new">New</SelectItem>
                <SelectItem value="qualified">Qualified</SelectItem>
                <SelectItem value="in-progress">In Progress</SelectItem>
                <SelectItem value="urgent">Urgent</SelectItem>
              </SelectContent>
            </Select>
            <Select>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Source" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sources</SelectItem>
                <SelectItem value="website">Website</SelectItem>
                <SelectItem value="social">Social Media</SelectItem>
                <SelectItem value="email">Email Campaign</SelectItem>
                <SelectItem value="referral">Referral</SelectItem>
              </SelectContent>
            </Select>
            <Select>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="attempts">Attempts</SelectItem>
                <SelectItem value="last-contact">Last Contact</SelectItem>
                <SelectItem value="name">Name</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {leads.map((lead) => (
              <Link key={lead.id} href={`/conversation/${lead.id}`}>
                <Card className="glass-card hover:bg-card/70 hover:shadow-lg hover:shadow-primary/5 transition-all duration-300 cursor-pointer h-full border border-border/50">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="min-w-0 flex-1">
                        <h3 className="font-semibold text-lg truncate mb-1">{lead.name}</h3>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Building2 className="h-4 w-4 flex-shrink-0" />
                          <span className="truncate">{lead.company}</span>
                        </div>
                      </div>
                      <Badge className={`${getStatusColor(lead.status)} text-xs px-3 py-1 ml-3 flex-shrink-0`}>
                        {lead.status}
                      </Badge>
                    </div>

                    <div className="space-y-2 mb-4">
                      <div className="flex items-center gap-3 text-sm">
                        <Mail className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                        <span className="truncate">{lead.email}</span>
                      </div>
                      <div className="flex items-center gap-3 text-sm">
                        <Phone className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                        <span className="truncate">{lead.phone}</span>
                      </div>
                    </div>

                    <div className="bg-muted/30 border border-border/30 p-4 rounded-lg mb-4">
                      <div className="flex items-center gap-2 mb-2">
                        <MessageSquare className="h-4 w-4 text-primary flex-shrink-0" />
                        <span className="text-sm font-medium">Initial Query</span>
                      </div>
                      <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed">{lead.initialQuery}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="text-center p-3 bg-muted/20 rounded-lg">
                        <div className="flex items-center justify-center gap-1 mb-1">
                          <BarChart3 className="h-4 w-4 text-accent" />
                          <span className="text-sm font-medium">Attempts Made</span>
                        </div>
                        <span className="text-lg font-bold text-accent">{lead.attempts}</span>
                      </div>
                      <div className="text-center p-3 bg-muted/20 rounded-lg">
                        <div className="flex items-center justify-center gap-1 mb-1">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm font-medium">Last Contact</span>
                        </div>
                        <span className="text-sm font-semibold">{lead.lastContact}</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-4 border-t border-border/50">
                      <span className="text-sm text-muted-foreground">Source: {lead.source}</span>
                      <span className="text-sm text-primary hover:text-primary/80 font-medium">
                        View conversation →
                      </span>
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
