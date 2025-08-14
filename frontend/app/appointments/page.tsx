"use client"

import type React from "react"

import { LayoutWrapper } from "@/components/layout-wrapper"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { format, addDays, startOfWeek, endOfWeek, eachDayOfInterval, isSameDay, parseISO } from "date-fns"
import { CalendarIcon, Plus, Clock, User, Search, Filter, MoreHorizontal, Phone, Mail, MapPin } from "lucide-react"
import { useState, useEffect, useCallback } from "react"
import { apiService, type AppointmentSlot, type SlotStatus, type Lead, type CreateBulkSlotsRequest, type BookSlotRequest } from "@/lib/api"
import { cn } from "@/lib/utils"

export default function AppointmentsPage() {
  const [isCreateSlotsOpen, setIsCreateSlotsOpen] = useState(false)
  const [isBookAppointmentOpen, setIsBookAppointmentOpen] = useState(false)
  const [selectedSlot, setSelectedSlot] = useState<AppointmentSlot | null>(null)
  const [appointments, setAppointments] = useState<AppointmentSlot[]>([])
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<SlotStatus | 'all'>('all')
  const [selectedDate, setSelectedDate] = useState<Date>(new Date())
  const [dateRange, setDateRange] = useState<{
    from: Date
    to: Date
  }>({
    from: startOfWeek(new Date()),
    to: endOfWeek(new Date())
  })
  
  // Create slots form state
  const [createSlotsForm, setCreateSlotsForm] = useState({
    start_date: format(new Date(), 'yyyy-MM-dd'),
    end_date: format(addDays(new Date(), 7), 'yyyy-MM-dd'),
    start_time_of_day: '09:00',
    end_time_of_day: '17:00',
    slot_duration_minutes: 30,
  })
  const [isCreatingSlots, setIsCreatingSlots] = useState(false)
  
  // Book appointment form state
  const [bookAppointmentForm, setBookAppointmentForm] = useState({
    lead_id: '',
    reason_for_visit: '',
    booked_by_method: 'manual',
  })
  const [isBookingAppointment, setIsBookingAppointment] = useState(false)

  // Fetch appointments from API
  const fetchAppointments = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const fetchedAppointments = await apiService.getAppointmentSlots(
        format(dateRange.from, 'yyyy-MM-dd'),
        format(dateRange.to, 'yyyy-MM-dd')
      )
      setAppointments(fetchedAppointments)
    } catch (err) {
      console.error('Error fetching appointments:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch appointments')
    } finally {
      setLoading(false)
    }
  }, [dateRange])

  // Fetch leads for booking appointments
  const fetchLeads = useCallback(async () => {
    try {
      const fetchedLeads = await apiService.getLeads()
      setLeads(fetchedLeads)
    } catch (err) {
      console.error('Error fetching leads:', err)
    }
  }, [])

  useEffect(() => {
    fetchAppointments()
    fetchLeads()
  }, [fetchAppointments, fetchLeads])

  // Filter appointments based on search and status
  const filteredAppointments = appointments.filter(appointment => {
    const matchesSearch = !searchTerm || 
      appointment.reason_for_visit?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      appointment.lead_id?.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesStatus = statusFilter === 'all' || appointment.status === statusFilter
    
    return matchesSearch && matchesStatus
  })

  // Handle create slots form submission
  const handleCreateSlots = async () => {
    try {
      setIsCreatingSlots(true)
      await apiService.createBulkSlots(createSlotsForm)
      setIsCreateSlotsOpen(false)
      fetchAppointments() // Refresh the list
      // Reset form
      setCreateSlotsForm({
        start_date: format(new Date(), 'yyyy-MM-dd'),
        end_date: format(addDays(new Date(), 7), 'yyyy-MM-dd'),
        start_time_of_day: '09:00',
        end_time_of_day: '17:00',
        slot_duration_minutes: 30,
      })
    } catch (err) {
      console.error('Error creating slots:', err)
      setError(err instanceof Error ? err.message : 'Failed to create appointment slots')
    } finally {
      setIsCreatingSlots(false)
    }
  }

  // Handle book appointment form submission
  const handleBookAppointment = async () => {
    if (!selectedSlot) return
    
    try {
      setIsBookingAppointment(true)
      await apiService.bookAppointmentSlot(selectedSlot.id, bookAppointmentForm)
      setIsBookAppointmentOpen(false)
      fetchAppointments() // Refresh the list
      // Reset form
      setBookAppointmentForm({
        lead_id: '',
        reason_for_visit: '',
        booked_by_method: 'manual',
      })
      setSelectedSlot(null)
    } catch (err) {
      console.error('Error booking appointment:', err)
      setError(err instanceof Error ? err.message : 'Failed to book appointment')
    } finally {
      setIsBookingAppointment(false)
    }
  }

  // Get status badge color
  const getStatusBadgeVariant = (status: SlotStatus) => {
    switch (status) {
      case 'available':
        return 'secondary'
      case 'booked':
        return 'default'
      case 'cancelled':
        return 'destructive'
      default:
        return 'outline'
    }
  }

  // Format time for display
  const formatTime = (dateString: string) => {
    return format(parseISO(dateString), 'HH:mm')
  }

  // Format date for display
  const formatDate = (dateString: string) => {
    return format(parseISO(dateString), 'MMM dd, yyyy')
  }

  // Get lead name by ID
  const getLeadName = (leadId?: string) => {
    if (!leadId) return 'N/A'
    const lead = leads.find(l => l.id === leadId)
    return lead ? `${lead.first_name || ''} ${lead.last_name || ''}`.trim() || lead.email : 'Unknown Lead'
  }

  return (
    <LayoutWrapper>
      <div className="flex-1 space-y-6 p-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Appointments</h1>
            <p className="text-muted-foreground">
              Manage appointment slots and bookings
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Dialog open={isCreateSlotsOpen} onOpenChange={setIsCreateSlotsOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Slots
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                  <DialogTitle>Create Appointment Slots</DialogTitle>
                  <DialogDescription>
                    Generate multiple appointment slots for a date range
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="start_date">Start Date</Label>
                      <Input
                        id="start_date"
                        type="date"
                        value={createSlotsForm.start_date}
                        onChange={(e) => setCreateSlotsForm(prev => ({ ...prev, start_date: e.target.value }))}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="end_date">End Date</Label>
                      <Input
                        id="end_date"
                        type="date"
                        value={createSlotsForm.end_date}
                        onChange={(e) => setCreateSlotsForm(prev => ({ ...prev, end_date: e.target.value }))}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="start_time">Start Time</Label>
                      <Input
                        id="start_time"
                        type="time"
                        value={createSlotsForm.start_time_of_day}
                        onChange={(e) => setCreateSlotsForm(prev => ({ ...prev, start_time_of_day: e.target.value }))}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <Label htmlFor="end_time">End Time</Label>
                      <Input
                        id="end_time"
                        type="time"
                        value={createSlotsForm.end_time_of_day}
                        onChange={(e) => setCreateSlotsForm(prev => ({ ...prev, end_time_of_day: e.target.value }))}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="duration">Slot Duration (minutes)</Label>
                    <Select
                      value={createSlotsForm.slot_duration_minutes.toString()}
                      onValueChange={(value) => setCreateSlotsForm(prev => ({ ...prev, slot_duration_minutes: parseInt(value) }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="15">15 minutes</SelectItem>
                        <SelectItem value="30">30 minutes</SelectItem>
                        <SelectItem value="45">45 minutes</SelectItem>
                        <SelectItem value="60">1 hour</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter>
                  <Button onClick={handleCreateSlots} disabled={isCreatingSlots}>
                    {isCreatingSlots ? 'Creating...' : 'Create Slots'}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Filters and Search */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="relative flex-1 max-w-sm min-w-[200px]">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search appointments..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as SlotStatus | 'all')}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="available">Available</SelectItem>
              <SelectItem value="booked">Booked</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
            </SelectContent>
          </Select>
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="justify-start text-left font-normal min-w-[200px]">
                <CalendarIcon className="mr-2 h-4 w-4" />
                {format(dateRange.from, 'MMM dd')} - {format(dateRange.to, 'MMM dd, yyyy')}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                initialFocus
                mode="range"
                selected={dateRange}
                onSelect={(range) => {
                  if (range?.from && range?.to) {
                    setDateRange({ from: range.from, to: range.to })
                  }
                }}
                numberOfMonths={2}
              />
            </PopoverContent>
          </Popover>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-destructive/15 text-destructive px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Appointments Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <Card key={i} className="animate-pulse">
                <CardHeader className="pb-3">
                  <div className="h-4 bg-muted rounded w-3/4"></div>
                  <div className="h-3 bg-muted rounded w-1/2"></div>
                </CardHeader>
                <CardContent>
                  <div className="h-3 bg-muted rounded w-full mb-2"></div>
                  <div className="h-3 bg-muted rounded w-2/3"></div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : filteredAppointments.length === 0 ? (
          <div className="text-center py-16">
            <h3 className="text-xl font-semibold mb-2">No appointments found</h3>
            <p className="text-muted-foreground mb-6 max-w-md mx-auto">
              {searchTerm || statusFilter !== 'all' 
                ? 'Try adjusting your search or filters to find what you\'re looking for.'
                : 'Get started by creating appointment slots for your clinic.'
              }
            </p>
            {!searchTerm && statusFilter === 'all' && (
              <Button 
                onClick={() => setIsCreateSlotsOpen(true)}
                className="gap-2"
              >
                <Plus className="h-4 w-4" />
                Create Your First Slots
              </Button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredAppointments.map((appointment) => (
              <Card key={appointment.id} className="hover:shadow-lg transition-all duration-200 hover:scale-[1.02]">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant={getStatusBadgeVariant(appointment.status)} className="text-xs">
                      {appointment.status}
                    </Badge>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {formatTime(appointment.start_time)}
                    </div>
                  </div>
                  <CardTitle className="text-base font-semibold">
                    {formatDate(appointment.start_time)}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {appointment.status === 'booked' ? (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm">
                        <User className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium truncate">
                          {getLeadName(appointment.lead_id)}
                        </span>
                      </div>
                      {appointment.reason_for_visit && (
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {appointment.reason_for_visit}
                        </p>
                      )}
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span>Booked via: {appointment.booked_by_method}</span>
                      </div>
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground py-2">
                      Available slot
                    </div>
                  )}
                  
                  {appointment.status === 'available' && (
                    <Button
                      size="sm"
                      className="w-full"
                      onClick={() => {
                        setSelectedSlot(appointment)
                        setIsBookAppointmentOpen(true)
                      }}
                    >
                      Book Appointment
                    </Button>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Book Appointment Dialog */}
        <Dialog open={isBookAppointmentOpen} onOpenChange={setIsBookAppointmentOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Book Appointment</DialogTitle>
              <DialogDescription>
                Book this appointment slot for a lead
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              {selectedSlot && (
                <div className="p-3 bg-muted rounded-lg">
                  <p className="text-sm font-medium">
                    {formatDate(selectedSlot.start_time)} at {formatTime(selectedSlot.start_time)}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Duration: {formatTime(selectedSlot.start_time)} - {formatTime(selectedSlot.end_time)}
                  </p>
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="lead">Select Lead</Label>
                <Select
                  value={bookAppointmentForm.lead_id}
                  onValueChange={(value) => setBookAppointmentForm(prev => ({ ...prev, lead_id: value }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a lead" />
                  </SelectTrigger>
                  <SelectContent>
                    {leads.map((lead) => (
                      <SelectItem key={lead.id} value={lead.id}>
                        {lead.first_name && lead.last_name 
                          ? `${lead.first_name} ${lead.last_name}`
                          : lead.email
                        }
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="reason">Reason for Visit</Label>
                <Textarea
                  id="reason"
                  placeholder="Enter the reason for this appointment..."
                  value={bookAppointmentForm.reason_for_visit}
                  onChange={(e) => setBookAppointmentForm(prev => ({ ...prev, reason_for_visit: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="method">Booking Method</Label>
                <Select
                  value={bookAppointmentForm.booked_by_method}
                  onValueChange={(value) => setBookAppointmentForm(prev => ({ ...prev, booked_by_method: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="manual">Manual</SelectItem>
                    <SelectItem value="phone">Phone</SelectItem>
                    <SelectItem value="email">Email</SelectItem>
                    <SelectItem value="website">Website</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleBookAppointment} disabled={isBookingAppointment}>
                {isBookingAppointment ? 'Booking...' : 'Book Appointment'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </LayoutWrapper>
  )
} 