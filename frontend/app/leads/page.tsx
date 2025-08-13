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
import { useState, useEffect, useCallback } from "react"
import { apiService, type Lead, type LeadStatus } from "@/lib/api"

export default function LeadsPage() {
  const [isAddLeadOpen, setIsAddLeadOpen] = useState(false)
  const [isImportOpen, setIsImportOpen] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<LeadStatus | 'all'>('all')
  
  // Add lead form state
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
    inquiry_notes: '',
  })
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [isSubmittingLead, setIsSubmittingLead] = useState(false)
  
  // CSV upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploadingCsv, setIsUploadingCsv] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  // Fetch leads from API
  const fetchLeads = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params: {
        status?: LeadStatus;
        search?: string;
      } = {}
      
      if (statusFilter !== 'all') {
        params.status = statusFilter as LeadStatus
      }
      
      if (searchTerm.trim()) {
        params.search = searchTerm.trim()
      }
      
      const fetchedLeads = await apiService.getLeads(params)
      setLeads(fetchedLeads)
    } catch (err) {
      console.error('Error fetching leads:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch leads')
    } finally {
      setLoading(false)
    }
  }, [searchTerm, statusFilter])

  // Debounced search effect
  useEffect(() => {
    const searchDebounce = setTimeout(() => {
      fetchLeads()
    }, searchTerm ? 300 : 0) // 300ms debounce for search, immediate for initial load and filters

    return () => clearTimeout(searchDebounce)
  }, [fetchLeads])

  // Form handlers
  const handleFormChange = (field: keyof typeof formData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    // Clear error for this field when user starts typing
    if (formErrors[field]) {
      setFormErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  const validateForm = () => {
    const errors: Record<string, string> = {}
    
    if (!formData.email.trim()) {
      errors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Please enter a valid email address'
    }
    
    if (!formData.first_name.trim() && !formData.last_name.trim()) {
      errors.name = 'At least first name or last name is required'
    }
    
    return errors
  }

  const resetForm = () => {
    setFormData({
      first_name: '',
      last_name: '',
      email: '',
      phone_number: '',
      inquiry_notes: '',
    })
    setFormErrors({})
  }

  const handleAddLead = async () => {
    const errors = validateForm()
    setFormErrors(errors)
    
    if (Object.keys(errors).length > 0) {
      return
    }
    
    try {
      setIsSubmittingLead(true)
      
      // Create the lead with current date as inquiry_date
      const leadData = {
        ...formData,
        inquiry_date: new Date().toISOString(),
      }
      
      await apiService.createLead(leadData)
      
      // Close dialog and reset form
      setIsAddLeadOpen(false)
      resetForm()
      
      // Refresh leads list
      fetchLeads()
      
    } catch (err) {
      console.error('Error creating lead:', err)
      setFormErrors({
        submit: err instanceof Error ? err.message : 'Failed to create lead'
      })
    } finally {
      setIsSubmittingLead(false)
    }
  }

  const getStatusColor = (status: LeadStatus) => {
    switch (status) {
      case "new":
        return "bg-purple-500/10 text-purple-500 border-purple-500/20"
      case "needs_immediate_attention":
        return "bg-red-500/10 text-red-500 border-red-500/20"
      case "nurturing":
        return "bg-blue-500/10 text-blue-500 border-blue-500/20"
      case "responded":
        return "bg-green-500/10 text-green-500 border-green-500/20"
      case "converted":
        return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
      case "archived_no_response":
        return "bg-gray-500/10 text-gray-500 border-gray-500/20"
      case "archived_not_interested":
        return "bg-slate-500/10 text-slate-500 border-slate-500/20"
      default:
        return "bg-gray-500/10 text-gray-500 border-gray-500/20"
    }
  }

  const getStatusLabel = (status: LeadStatus) => {
    switch (status) {
      case "new":
        return "New"
      case "needs_immediate_attention":
        return "Urgent"
      case "nurturing":
        return "Nurturing"
      case "responded":
        return "Responded"
      case "converted":
        return "Converted"
      case "archived_no_response":
        return "No Response"
      case "archived_not_interested":
        return "Not Interested"
      default:
        return status
    }
  }

  // CSV upload handlers
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
    
    const files = e.dataTransfer.files
    if (files && files[0]) {
      const file = files[0]
      if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        setSelectedFile(file)
        setUploadError(null)
      } else {
        setUploadError('Please select a CSV file')
      }
    }
  }

  const handleFileAreaClick = () => {
    const fileInput = document.getElementById("csv-upload") as HTMLInputElement
    if (fileInput) {
      fileInput.click()
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        setSelectedFile(file)
        setUploadError(null)
      } else {
        setUploadError('Please select a CSV file')
        setSelectedFile(null)
      }
    }
  }

  const handleCsvUpload = async () => {
    if (!selectedFile) {
      setUploadError('Please select a CSV file')
      return
    }

    try {
      setIsUploadingCsv(true)
      setUploadError(null)

      const uploadedLeads = await apiService.uploadLeadsCsv(selectedFile)
      
      // Close dialog and reset state
      setIsImportOpen(false)
      setSelectedFile(null)
      
      // Refresh leads list
      fetchLeads()
      
      console.log(`Successfully uploaded ${uploadedLeads.length} leads`)
      
    } catch (err) {
      console.error('Error uploading CSV:', err)
      setUploadError(err instanceof Error ? err.message : 'Failed to upload CSV file')
    } finally {
      setIsUploadingCsv(false)
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
              <Dialog open={isImportOpen} onOpenChange={(open: boolean) => {
                setIsImportOpen(open)
                if (!open) {
                  setSelectedFile(null)
                  setUploadError(null)
                }
              }}>
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
                      Upload a CSV file with your leads. Make sure your file includes the required columns.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div
                      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
                        dragActive ? "border-primary bg-primary/5" : 
                        selectedFile ? "border-green-500 bg-green-50 dark:bg-green-500/10" :
                        "border-border hover:border-primary/50"
                      }`}
                      onDragEnter={handleDrag}
                      onDragLeave={handleDrag}
                      onDragOver={handleDrag}
                      onDrop={handleDrop}
                      onClick={handleFileAreaClick}
                    >
                      {selectedFile ? (
                        <>
                          <FileText className="h-12 w-12 mx-auto mb-4 text-green-600" />
                          <div className="space-y-2">
                            <p className="text-sm font-medium text-green-600">{selectedFile.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {(selectedFile.size / 1024).toFixed(1)} KB - Click to change file
                            </p>
                          </div>
                        </>
                      ) : (
                        <>
                          <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                          <div className="space-y-2">
                            <p className="text-sm font-medium">Drop your CSV file here</p>
                            <p className="text-xs text-muted-foreground">or click to browse</p>
                          </div>
                        </>
                      )}
                      <Input 
                        type="file" 
                        accept=".csv" 
                        className="hidden" 
                        id="csv-upload" 
                        onChange={handleFileSelect}
                      />
                    </div>
                    
                    {uploadError && (
                      <p className="text-sm text-red-500">{uploadError}</p>
                    )}
                    
                    <div className="text-xs text-muted-foreground space-y-1">
                      <p className="font-medium">Expected CSV columns:</p>
                      <p>• <strong>email</strong> (required) - Contact email address</p>
                      <p>• <strong>first_name</strong> (optional) - First name</p>
                      <p>• <strong>last_name</strong> (optional) - Last name</p>
                      <p>• <strong>phone_number</strong> (optional) - Phone number</p>
                      <p>• <strong>inquiry_notes</strong> (optional) - Initial inquiry or notes</p>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => {
                      setIsImportOpen(false)
                      setSelectedFile(null)
                      setUploadError(null)
                    }}>
                      Cancel
                    </Button>
                    <Button onClick={handleCsvUpload} disabled={!selectedFile || isUploadingCsv}>
                      {isUploadingCsv ? 'Uploading...' : 'Upload CSV'}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              <Dialog open={isAddLeadOpen} onOpenChange={(open: boolean) => {
                setIsAddLeadOpen(open)
                if (!open) {
                  resetForm()
                }
              }}>
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
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="first-name">First Name</Label>
                        <Input 
                          id="first-name" 
                          placeholder="First name"
                          value={formData.first_name}
                          onChange={(e) => handleFormChange('first_name', e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="last-name">Last Name</Label>
                        <Input 
                          id="last-name" 
                          placeholder="Last name"
                          value={formData.last_name}
                          onChange={(e) => handleFormChange('last_name', e.target.value)}
                        />
                      </div>
                    </div>
                    {formErrors.name && (
                      <p className="text-sm text-red-500">{formErrors.name}</p>
                    )}
                    
                    <div className="space-y-2">
                      <Label htmlFor="email">Email Address *</Label>
                      <Input 
                        id="email" 
                        type="email" 
                        placeholder="Enter email address"
                        value={formData.email}
                        onChange={(e) => handleFormChange('email', e.target.value)}
                      />
                      {formErrors.email && (
                        <p className="text-sm text-red-500">{formErrors.email}</p>
                      )}
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="phone">Phone Number</Label>
                      <Input 
                        id="phone" 
                        type="tel" 
                        placeholder="Enter phone number"
                        value={formData.phone_number}
                        onChange={(e) => handleFormChange('phone_number', e.target.value)}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="inquiry">Inquiry Notes</Label>
                      <Textarea
                        id="inquiry"
                        placeholder="What is the lead interested in or asking about?"
                        className="min-h-[80px]"
                        value={formData.inquiry_notes}
                        onChange={(e) => handleFormChange('inquiry_notes', e.target.value)}
                      />
                    </div>
                    
                    {formErrors.submit && (
                      <p className="text-sm text-red-500">{formErrors.submit}</p>
                    )}
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => {
                      setIsAddLeadOpen(false)
                      resetForm()
                    }}>
                      Cancel
                    </Button>
                    <Button onClick={handleAddLead} disabled={isSubmittingLead}>
                      {isSubmittingLead ? 'Adding...' : 'Add Lead'}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
          </div>

          {/* Inline Filters */}
          <div className="flex flex-wrap items-center gap-4">
            <div className="relative flex-1 min-w-[250px]">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input 
                placeholder="Search leads by name, email, or notes..." 
                className="pl-10" 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Select value={statusFilter} onValueChange={(value: string) => setStatusFilter(value as LeadStatus | 'all')}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="new">New</SelectItem>
                <SelectItem value="needs_immediate_attention">Urgent</SelectItem>
                <SelectItem value="nurturing">Nurturing</SelectItem>
                <SelectItem value="responded">Responded</SelectItem>
                <SelectItem value="converted">Converted</SelectItem>
                <SelectItem value="archived_no_response">No Response</SelectItem>
                <SelectItem value="archived_not_interested">Not Interested</SelectItem>
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
          {loading && (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <Card key={i} className="glass-card border border-border/50">
                  <CardContent className="p-6">
                    <div className="animate-pulse space-y-4">
                      <div className="flex items-start justify-between">
                        <div className="space-y-2 flex-1">
                          <div className="h-5 bg-muted rounded w-3/4"></div>
                          <div className="h-4 bg-muted rounded w-1/2"></div>
                        </div>
                        <div className="h-6 bg-muted rounded w-20"></div>
                      </div>
                      <div className="space-y-2">
                        <div className="h-4 bg-muted rounded w-full"></div>
                        <div className="h-4 bg-muted rounded w-3/4"></div>
                      </div>
                      <div className="h-20 bg-muted rounded"></div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="h-16 bg-muted rounded"></div>
                        <div className="h-16 bg-muted rounded"></div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {error && (
            <div className="text-center py-12">
              <div className="text-red-500 mb-2">Error loading leads</div>
              <div className="text-sm text-muted-foreground mb-4">{error}</div>
              <Button onClick={() => window.location.reload()}>Try Again</Button>
            </div>
          )}

          {!loading && !error && leads.length === 0 && (
            <div className="text-center py-12">
              <div className="text-muted-foreground mb-2">No leads found</div>
              <div className="text-sm text-muted-foreground">Start by adding your first lead or importing a CSV file.</div>
            </div>
          )}

          {!loading && !error && leads.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {leads.map((lead) => {
                const fullName = [lead.first_name, lead.last_name].filter(Boolean).join(' ') || 'Unknown Lead'
                const formatDate = (dateString: string) => {
                  const date = new Date(dateString)
                  const now = new Date()
                  const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
                  
                  if (diffInHours < 1) return 'Less than 1 hour ago'
                  if (diffInHours < 24) return `${diffInHours} hours ago`
                  
                  const diffInDays = Math.floor(diffInHours / 24)
                  if (diffInDays < 7) return `${diffInDays} days ago`
                  
                  return date.toLocaleDateString()
                }

                return (
                  <Link key={lead.id} href={`/conversation/${lead.id}`}>
                    <Card className="glass-card hover:bg-card/70 hover:shadow-lg hover:shadow-primary/5 transition-all duration-300 cursor-pointer h-full border border-border/50">
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between mb-4">
                          <div className="min-w-0 flex-1">
                            <h3 className="font-semibold text-lg truncate mb-1">{fullName}</h3>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <Building2 className="h-4 w-4 flex-shrink-0" />
                              <span className="truncate">Lead ID: {lead.lead_id}</span>
                            </div>
                          </div>
                          <Badge className={`${getStatusColor(lead.status)} text-xs px-3 py-1 ml-3 flex-shrink-0`}>
                            {getStatusLabel(lead.status)}
                          </Badge>
                        </div>

                        <div className="space-y-2 mb-4">
                          <div className="flex items-center gap-3 text-sm">
                            <Mail className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                            <span className="truncate">{lead.email}</span>
                          </div>
                          {lead.phone_number && (
                            <div className="flex items-center gap-3 text-sm">
                              <Phone className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                              <span className="truncate">{lead.phone_number}</span>
                            </div>
                          )}
                        </div>

                        {lead.inquiry_notes && (
                          <div className="bg-muted/30 border border-border/30 p-4 rounded-lg mb-4">
                            <div className="flex items-center gap-2 mb-2">
                              <MessageSquare className="h-4 w-4 text-primary flex-shrink-0" />
                              <span className="text-sm font-medium">Inquiry Notes</span>
                            </div>
                            <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed">{lead.inquiry_notes}</p>
                          </div>
                        )}

                        <div className="grid grid-cols-2 gap-4 mb-4">
                          <div className="text-center p-3 bg-muted/20 rounded-lg">
                            <div className="flex items-center justify-center gap-1 mb-1">
                              <BarChart3 className="h-4 w-4 text-accent" />
                              <span className="text-sm font-medium">Attempts</span>
                            </div>
                            <span className="text-lg font-bold text-accent">{lead.nurture_attempts}</span>
                          </div>
                          <div className="text-center p-3 bg-muted/20 rounded-lg">
                            <div className="flex items-center justify-center gap-1 mb-1">
                              <Clock className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm font-medium">Last Updated</span>
                            </div>
                            <span className="text-sm font-semibold">{formatDate(lead.updated_at)}</span>
                          </div>
                        </div>

                        <div className="flex items-center justify-between pt-4 border-t border-border/50">
                          <span className="text-sm text-muted-foreground">Created: {new Date(lead.created_at).toLocaleDateString()}</span>
                          <span className="text-sm text-primary hover:text-primary/80 font-medium">
                            View conversation →
                          </span>
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </LayoutWrapper>
  )
}
