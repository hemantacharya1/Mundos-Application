// API Service for Bright Smile Clinic MVP
// Base URL will be stored in environment variables

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

// Types based on backend models
export interface Lead {
  id: string; // UUID
  lead_id: string; // String(20)
  first_name?: string; // String(100)
  last_name?: string; // String(100)
  email: string; // String(255), required
  phone_number?: string; // String(50)
  inquiry_notes?: string; // Text
  inquiry_date: string; // DateTime(timezone=True), required
  status: LeadStatus; // Enum(LeadStatusEnum), required
  nurture_attempts: number; // Integer, required, default 0
  ai_summary?: string; // Text, nullable
  ai_drafted_reply?: string; // Text, nullable
  created_at: string; // DateTime(timezone=True), server_default=func.now()
  updated_at: string; // DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
}

export interface LeadCreate {
  first_name?: string;
  last_name?: string;
  email: string; // required
  phone_number?: string;
  inquiry_notes?: string;
  inquiry_date: string; // required
}

export type LeadStatus = 
  | 'new'
  | 'needs_immediate_attention'
  | 'nurturing'
  | 'responded'
  | 'converted'
  | 'archived_no_response'
  | 'archived_not_interested';

export type CommType = 'email' | 'sms' | 'note' | 'phone_call';

export type CommDirection = 'outgoing_auto' | 'outgoing_manual' | 'incoming';

export interface Communication {
  id: string; // UUID
  lead_id: string; // UUID, required
  type: CommType; // Enum(CommTypeEnum), required
  direction: CommDirection; // Enum(CommDirectionEnum), required
  content: string; // Text, required
  sent_at: string; // DateTime(timezone=True), server_default=func.now()
}

export interface DashboardMetrics {
  total_active_leads: number;
  needs_attention_count: number;
  responded_count: number;
  nurturing_count: number;
  converted_this_month: number;
  conversion_rate_percent: number;
}

// Advanced Dashboard Metrics Types
export interface LeadStatusDistribution {
  status: string;
  count: number;
}

export interface DailyLeadVolume {
  date: string;
  count: number;
}

export interface LeadVelocity {
  status: string;
  avg_hours: number;
}

export interface NurtureAttempts {
  attempts: number;
  count: number;
}

export interface CommunicationTypes {
  type: string;
  count: number;
}

export interface ResponseTimeStats {
  min: number;
  max: number;
  median: number;
  q1: number;
  q3: number;
}

export interface LeadQuality {
  notes_length: number;
  email_completeness: number;
  status: string;
  quality_score: number;
}

export interface HourlyPattern {
  hour: number;
  count: number;
}

export interface AiUtilization {
  total_leads: number;
  ai_summary_rate: number;
  ai_draft_rate: number;
}

export interface ConversionFunnel {
  stage: string;
  count: number;
  percentage: number;
}

export interface AdvancedDashboardMetrics {
  lead_status_distribution: LeadStatusDistribution[]; // Pie Chart
  daily_lead_volume: DailyLeadVolume[]; // Line Chart
  lead_velocity: LeadVelocity[]; // Bar Chart
  nurture_attempts: NurtureAttempts[]; // Histogram/Bar Chart
  communication_types: CommunicationTypes[]; // Donut Chart
  response_time_stats: ResponseTimeStats; // Box Plot
  lead_quality: LeadQuality[]; // Scatter Plot
  hourly_pattern: HourlyPattern[]; // Heatmap
  ai_utilization: AiUtilization; // Progress Bars
  conversion_funnel: ConversionFunnel[]; // Funnel Chart
}

// Appointment Types
export interface AppointmentSlot {
  id: string;
  start_time: string;
  end_time: string;
  status: SlotStatus;
  lead_id?: string;
  reason_for_visit?: string;
  booked_by_method?: string;
  created_at: string;
  updated_at: string;
}

export type SlotStatus = 'available' | 'booked' | 'cancelled';

export interface CreateBulkSlotsRequest {
  start_date: string;
  end_date: string;
  start_time_of_day: string;
  end_time_of_day: string;
  slot_duration_minutes: number;
}

export interface BookSlotRequest {
  lead_id: string;
  reason_for_visit: string;
  booked_by_method: string;
}

// Knowledge Base Types
export interface KnowledgeBaseEntry {
  title: string;
  chunks: Array<{
    id: string;
    content: string;
    chunk_id: string;
    created_at: string;
    updated_at: string;
  }>;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeBaseCreate {
  title: string;
  content: string;
}

export interface KnowledgeBaseSearch {
  query: string;
  top_k: number;
}

export interface SearchResult {
  chunk_id: string;
  score: number;
  content: string;
  title: string;
  chunk_index: number;
}

export interface SearchResponse {
  results: SearchResult[];
  query: string;
  total_results: number;
}

// API Service Class
class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response.json();
  }

  // Dashboard endpoints
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    return this.request<DashboardMetrics>('/api/dashboard/metrics');
  }

  async getAdvancedDashboardMetrics(): Promise<AdvancedDashboardMetrics> {
    return this.request<AdvancedDashboardMetrics>('/api/dashboard/advanced-metrics');
  }

  // Leads endpoints
  async getLead(leadId: string): Promise<Lead> {
    return this.request<Lead>(`/api/leads/${leadId}`)
  }

  async getLeads(params?: {
    status?: LeadStatus;
    search?: string;
    page?: number;
    limit?: number;
  }): Promise<Lead[]> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.append('status', params.status);
    if (params?.search) searchParams.append('search', params.search);
    if (params?.page) searchParams.append('page', params.page.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());

    const queryString = searchParams.toString();
    const endpoint = `/api/leads${queryString ? `?${queryString}` : ''}`;
    
    return this.request<Lead[]>(endpoint);
  }

  async createLead(lead: LeadCreate): Promise<Lead> {
    return this.request<Lead>('/api/leads', {
      method: 'POST',
      body: JSON.stringify(lead),
    });
  }

  async updateLeadStatus(leadId: string, status: LeadStatus): Promise<Lead> {
    return this.request<Lead>(`/api/leads/${leadId}/status?status_update=${status}`, {
      method: 'PUT',
    });
  }

  async getLeadCommunications(leadId: string): Promise<Communication[]> {
    return this.request<Communication[]>(`/api/leads/${leadId}/communications`);
  }



  async sendManualReply(leadId: string, content: string): Promise<void> {
    return this.request<void>(`/api/leads/${leadId}/reply`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  }

  // Appointment endpoints
  async getAppointmentSlots(startDate: string, endDate: string): Promise<AppointmentSlot[]> {
    const searchParams = new URLSearchParams();
    searchParams.append('start_date', startDate);
    searchParams.append('end_date', endDate);
    
    return this.request<AppointmentSlot[]>(`/api/appointments?${searchParams.toString()}`);
  }

  async createBulkSlots(request: CreateBulkSlotsRequest): Promise<{ status: string; message: string }> {
    return this.request<{ status: string; message: string }>('/api/appointments/create-bulk-slots', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async bookAppointmentSlot(slotId: string, request: BookSlotRequest): Promise<AppointmentSlot> {
    return this.request<AppointmentSlot>(`/api/appointments/${slotId}/book`, {
      method: 'PUT',
      body: JSON.stringify(request),
    });
  }

  async uploadLeadsCsv(file: File): Promise<Lead[]> {
    const formData = new FormData();
    formData.append('file', file);

    const url = `${this.baseUrl}/api/leads/upload`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  // Testing endpoints
  async testAiCall(leadId: string): Promise<void> {
    return this.request<void>(`/api/leads/${leadId}/test-ai-call`, {
      method: 'POST',
    });
  }

  // Knowledge Base endpoints
  async getKnowledgeBaseEntries(): Promise<KnowledgeBaseEntry[]> {
    return this.request<KnowledgeBaseEntry[]>('/api/knowledge-base');
  }

  async createKnowledgeBaseEntry(entry: KnowledgeBaseCreate): Promise<KnowledgeBaseEntry> {
    return this.request<KnowledgeBaseEntry>('/api/knowledge-base', {
      method: 'POST',
      body: JSON.stringify(entry),
    });
  }

  async updateKnowledgeBaseEntry(title: string, content: string): Promise<KnowledgeBaseEntry> {
    return this.request<KnowledgeBaseEntry>('/api/knowledge-base', {
      method: 'POST',
      body: JSON.stringify({ title, content }),
    });
  }

  async searchKnowledgeBase(searchRequest: KnowledgeBaseSearch): Promise<SearchResponse> {
    return this.request<SearchResponse>('/api/knowledge-base/search', {
      method: 'POST',
      body: JSON.stringify(searchRequest),
    });
  }

  async deleteKnowledgeBaseEntry(title: string): Promise<{ message: string }> {
    const encodedTitle = encodeURIComponent(title);
    return this.request<{ message: string }>(`/api/knowledge-base/${encodedTitle}`, {
      method: 'DELETE',
    });
  }

  // Root endpoint
  async getRoot(): Promise<any> {
    return this.request<any>('/');
  }
}

// Export singleton instance
export const apiService = new ApiService();

// Export the class for testing or custom instances
export { ApiService }; 