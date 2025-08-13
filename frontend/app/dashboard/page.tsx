"use client"

import { LayoutWrapper } from "@/components/layout-wrapper"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Users, UserCheck, TrendingUp, Clock, Activity, CheckCircle, AlertTriangle, Phone, BarChart3, PieChart, LineChart, Zap, Target, MessageSquare } from "lucide-react"
import { useEffect, useState, useRef } from "react"
import { apiService, DashboardMetrics, AdvancedDashboardMetrics } from "@/lib/api"
import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  LineChart as RechartsLineChart,
  Line,
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  FunnelChart,
  Funnel,
  LabelList
} from "recharts"

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [advancedMetrics, setAdvancedMetrics] = useState<AdvancedDashboardMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true)
        const [basicData, advancedData] = await Promise.all([
          apiService.getDashboardMetrics(),
          apiService.getAdvancedDashboardMetrics()
        ])
        setMetrics(basicData)
        setAdvancedMetrics(advancedData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch metrics')
      } finally {
        setLoading(false)
      }
    }

    fetchMetrics()
  }, [])

  // Chart color schemes matching the theme
  const COLORS = {
    primary: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],
    status: {
      new: '#6b7280',
      needs_immediate_attention: '#ef4444',
      responded: '#10b981',
      nurturing: '#f59e0b',
      converted: '#8b5cf6',
      archived_no_response: '#9ca3af',
      archived_not_interested: '#6b7280'
    }
  }

  // Custom tooltip component for better dark mode support
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border border-border rounded-lg shadow-lg p-3">
          <p className="text-foreground font-medium">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {`${entry.name}: ${entry.value}`}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  // Custom legend component
  const CustomLegend = ({ payload }: any) => {
    return (
      <ul className="flex flex-wrap justify-center gap-4 mt-4">
        {payload?.map((entry: any, index: number) => (
          <li key={index} className="flex items-center gap-2 text-sm">
            <div 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-foreground capitalize">
              {entry.value.replace(/_/g, ' ')}
            </span>
          </li>
        ))}
      </ul>
    )
  }

  // Format status names for display
  const formatStatusName = (status: string) => {
    return status.replace(/_/g, ' ').split(' ').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    })
  }

  const metricsData = [
    {
      title: "Total Active Leads",
      value: metrics?.total_active_leads?.toLocaleString() || "0",
      change: "+12.5%",
      trend: "up",
      icon: Users,
      color: "text-blue-500",
    },
    {
      title: "Needs Attention",
      value: metrics?.needs_attention_count?.toLocaleString() || "0",
      change: "+8.2%",
      trend: "up",
      icon: AlertTriangle,
      color: "text-red-500",
    },
    {
      title: "Responded",
      value: metrics?.responded_count?.toLocaleString() || "0",
      change: "+5.3%",
      trend: "up",
      icon: CheckCircle,
      color: "text-green-500",
    },
    {
      title: "Nurturing",
      value: metrics?.nurturing_count?.toLocaleString() || "0",
      change: "+3.1%",
      trend: "up",
      icon: Clock,
      color: "text-yellow-500",
    },
    {
      title: "Converted This Month",
      value: metrics?.converted_this_month?.toLocaleString() || "0",
      change: "+15.2%",
      trend: "up",
      icon: TrendingUp,
      color: "text-purple-500",
    },
    {
      title: "Conversion Rate",
      value: `${metrics?.conversion_rate_percent || 0}%`,
      change: "+2.1%",
      trend: "up",
      icon: UserCheck,
      color: "text-teal-500",
    },
  ]

  const recentActivity = [
    {
      type: "qualified",
      message: "Sarah Johnson from TechCorp qualified as high-priority lead",
      time: "2 minutes ago",
      icon: CheckCircle,
      color: "text-green-500",
    },
    {
      type: "handoff",
      message: "Lead Michael Chen handed off to sales team",
      time: "5 minutes ago",
      icon: UserCheck,
      color: "text-blue-500",
    },
    {
      type: "urgent",
      message: "Urgent lead Emma Wilson requires immediate attention",
      time: "8 minutes ago",
      icon: AlertTriangle,
      color: "text-red-500",
    },
    {
      type: "call",
      message: "Scheduled call with David Park for tomorrow 2 PM",
      time: "12 minutes ago",
      icon: Phone,
      color: "text-purple-500",
    },
  ]

  return (
    <LayoutWrapper>
      <div className="h-full flex flex-col p-4 space-y-4">
        {/* Header */}
        <div className="flex-shrink-0">
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Monitor your AI lead management performance</p>
        </div>

        <div 
          className="flex-1 overflow-y-auto space-y-4 scrollbar-hide" 
          style={{
            scrollbarWidth: 'none',
            msOverflowStyle: 'none',
          }}
        >
          {/* Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
            {loading ? (
              // Loading skeleton
              Array.from({ length: 6 }).map((_, index) => (
                <Card key={index} className="glass-card">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-2">
                        <div className="h-4 bg-muted rounded w-20 animate-pulse" />
                        <div className="h-8 bg-muted rounded w-16 animate-pulse" />
                        <div className="h-6 bg-muted rounded w-12 animate-pulse" />
                      </div>
                      <div className="h-8 w-8 bg-muted rounded animate-pulse" />
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : error ? (
              // Error state
              <div className="col-span-full">
                <Card className="glass-card">
                  <CardContent className="p-4">
                    <p className="text-red-500 text-center">Error loading metrics: {error}</p>
                  </CardContent>
                </Card>
              </div>
            ) : (
              // Actual metrics
              metricsData.map((metric, index) => (
                <Card key={index} className="glass-card hover:bg-card/70 transition-all duration-300">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">{metric.title}</p>
                        <p className="text-2xl font-bold">{metric.value}</p>
                        <Badge variant={metric.trend === "up" ? "default" : "secondary"} className="mt-2">
                          {metric.change}
                        </Badge>
                      </div>
                      <metric.icon className={`h-8 w-8 ${metric.color}`} />
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>

          {/* Advanced Analytics Charts */}
          {!loading && !error && advancedMetrics && (
            <div className="space-y-4">
              <div>
                <h2 className="text-2xl font-bold mb-2">Analytics & Insights</h2>
                <p className="text-muted-foreground mb-4">Detailed performance metrics and trends</p>
              </div>

              {/* First Row - Lead Distribution and Daily Trends */}
              <div className="grid lg:grid-cols-2 gap-4">
                {/* Lead Status Distribution - Pie Chart */}
                <Card className="glass-card">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <PieChart className="h-5 w-5 text-blue-500" />
                      Lead Status Distribution
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <RechartsPieChart>
                          <Pie
                            data={advancedMetrics.lead_status_distribution.map(item => ({
                              ...item,
                              name: formatStatusName(item.status)
                            }))}
                            cx="50%"
                            cy="40%"
                            innerRadius={50}
                            outerRadius={80}
                            dataKey="count"
                            nameKey="name"
                            label={({ value, percent }) => `${value} (${(percent * 100).toFixed(0)}%)`}
                          >
                            {advancedMetrics.lead_status_distribution.map((entry, index) => (
                              <Cell 
                                key={`cell-${index}`} 
                                fill={COLORS.status[entry.status as keyof typeof COLORS.status] || COLORS.primary[index % COLORS.primary.length]}
                              />
                            ))}
                          </Pie>
                          <Tooltip content={<CustomTooltip />} />
                          <Legend content={<CustomLegend />} />
                        </RechartsPieChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                {/* Daily Lead Volume - Line Chart */}
                <Card className="glass-card">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <LineChart className="h-5 w-5 text-green-500" />
                      Daily Lead Volume (7 Days)
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <RechartsLineChart 
                          data={advancedMetrics.daily_lead_volume.map(item => ({
                            ...item,
                            formattedDate: formatDate(item.date)
                          }))}
                          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted))" />
                          <XAxis 
                            dataKey="formattedDate" 
                            stroke="hsl(var(--foreground))"
                            fontSize={12}
                            angle={-45}
                            textAnchor="end"
                            height={60}
                          />
                          <YAxis 
                            stroke="hsl(var(--foreground))" 
                            fontSize={12}
                            label={{ value: 'Leads', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: 'hsl(var(--foreground))' } }}
                          />
                          <Tooltip content={<CustomTooltip />} />
                          <Line 
                            type="monotone" 
                            dataKey="count" 
                            name="Daily Leads"
                            stroke="#10b981" 
                            strokeWidth={3}
                            dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
                            activeDot={{ r: 6, stroke: '#10b981', strokeWidth: 2 }}
                          />
                        </RechartsLineChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Second Row - Lead Velocity and Communication Types */}
              <div className="grid lg:grid-cols-2 gap-4">
                {/* Lead Velocity - Bar Chart */}
                <Card className="glass-card">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <BarChart3 className="h-5 w-5 text-purple-500" />
                      Lead Velocity (Hours by Status)
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <RechartsBarChart 
                          data={advancedMetrics.lead_velocity.map(item => ({
                            ...item,
                            formattedStatus: formatStatusName(item.status)
                          }))}
                          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted))" />
                          <XAxis 
                            dataKey="formattedStatus" 
                            stroke="hsl(var(--foreground))"
                            fontSize={12}
                            angle={-45}
                            textAnchor="end"
                            height={60}
                          />
                          <YAxis 
                            stroke="hsl(var(--foreground))" 
                            fontSize={12}
                            label={{ value: 'Hours', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: 'hsl(var(--foreground))' } }}
                          />
                          <Tooltip content={<CustomTooltip />} />
                          <Bar 
                            dataKey="avg_hours" 
                            name="Average Hours"
                            fill="#8b5cf6" 
                            radius={[4, 4, 0, 0]} 
                          />
                        </RechartsBarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                {/* Communication Types - Donut Chart */}
                <Card className="glass-card">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <MessageSquare className="h-5 w-5 text-teal-500" />
                      Communication Breakdown
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <RechartsPieChart>
                          <Pie
                            data={advancedMetrics.communication_types.map(item => ({
                              ...item,
                              name: item.type.replace(/_/g, ' ').split(' ').map(word => 
                                word.charAt(0).toUpperCase() + word.slice(1)
                              ).join(' ')
                            }))}
                            cx="50%"
                            cy="40%"
                            innerRadius={60}
                            outerRadius={90}
                            dataKey="count"
                            nameKey="name"
                            label={({ value, percent }) => `${value} (${(percent * 100).toFixed(0)}%)`}
                          >
                            {advancedMetrics.communication_types.map((entry, index) => (
                              <Cell 
                                key={`cell-${index}`} 
                                fill={COLORS.primary[index % COLORS.primary.length]}
                              />
                            ))}
                          </Pie>
                          <Tooltip content={<CustomTooltip />} />
                          <Legend content={<CustomLegend />} />
                        </RechartsPieChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Third Row - AI Utilization and Conversion Funnel */}
              <div className="grid lg:grid-cols-2 gap-4">
                {/* AI Utilization - Progress Bars */}
                <Card className="glass-card">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Zap className="h-5 w-5 text-yellow-500" />
                      AI Utilization Metrics
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>AI Summary Generation</span>
                        <span className="font-medium">{advancedMetrics.ai_utilization.ai_summary_rate}%</span>
                      </div>
                      <Progress value={advancedMetrics.ai_utilization.ai_summary_rate} className="h-2" />
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>AI Draft Generation</span>
                        <span className="font-medium">{advancedMetrics.ai_utilization.ai_draft_rate}%</span>
                      </div>
                      <Progress value={advancedMetrics.ai_utilization.ai_draft_rate} className="h-2" />
                    </div>
                    <div className="pt-4 border-t border-border/50">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Total Leads Processed</span>
                        <span className="font-bold text-lg">{advancedMetrics.ai_utilization.total_leads.toLocaleString()}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Conversion Funnel */}
                <Card className="glass-card">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Target className="h-5 w-5 text-red-500" />
                      Lead Conversion Funnel
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {advancedMetrics.conversion_funnel.map((stage, index) => (
                        <div key={stage.stage} className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                          <div className="flex items-center gap-3">
                            <div 
                              className="w-4 h-4 rounded-full"
                              style={{ 
                                backgroundColor: COLORS.status[stage.stage as keyof typeof COLORS.status] || COLORS.primary[index % COLORS.primary.length]
                              }}
                            />
                            <span className="text-sm font-medium capitalize">
                              {stage.stage.replace(/_/g, ' ')}
                            </span>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-bold">{stage.count.toLocaleString()}</div>
                            <div className="text-xs text-muted-foreground">{stage.percentage}%</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Fourth Row - Nurture Attempts and Response Time */}
              <div className="grid lg:grid-cols-2 gap-4">
                {/* Nurture Attempts Distribution - Histogram */}
                <Card className="glass-card">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <TrendingUp className="h-5 w-5 text-orange-500" />
                      Nurture Attempts Distribution
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <RechartsBarChart 
                          data={advancedMetrics.nurture_attempts}
                          margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted))" />
                          <XAxis 
                            dataKey="attempts" 
                            stroke="hsl(var(--foreground))"
                            fontSize={12}
                            label={{ value: 'Number of Attempts', position: 'insideBottom', offset: -10, style: { textAnchor: 'middle', fill: 'hsl(var(--foreground))' } }}
                          />
                          <YAxis 
                            stroke="hsl(var(--foreground))" 
                            fontSize={12}
                            label={{ value: 'Leads', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: 'hsl(var(--foreground))' } }}
                          />
                          <Tooltip content={<CustomTooltip />} />
                          <Bar 
                            dataKey="count" 
                            name="Number of Leads"
                            fill="#f59e0b" 
                            radius={[4, 4, 0, 0]} 
                          />
                        </RechartsBarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                {/* Response Time Stats - Box Plot Representation */}
                <Card className="glass-card">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Clock className="h-5 w-5 text-cyan-500" />
                      Response Time Distribution (Hours)
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="text-center p-3 rounded-lg bg-muted/30">
                          <div className="text-2xl font-bold text-green-500">
                            {advancedMetrics.response_time_stats.min.toFixed(1)}
                          </div>
                          <div className="text-xs text-muted-foreground">Minimum</div>
                        </div>
                        <div className="text-center p-3 rounded-lg bg-muted/30">
                          <div className="text-2xl font-bold text-red-500">
                            {advancedMetrics.response_time_stats.max.toFixed(1)}
                          </div>
                          <div className="text-xs text-muted-foreground">Maximum</div>
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="text-center p-3 rounded-lg bg-muted/30">
                          <div className="text-lg font-bold text-blue-500">
                            {advancedMetrics.response_time_stats.q1.toFixed(1)}
                          </div>
                          <div className="text-xs text-muted-foreground">Q1</div>
                        </div>
                        <div className="text-center p-3 rounded-lg bg-muted/30">
                          <div className="text-lg font-bold text-purple-500">
                            {advancedMetrics.response_time_stats.median.toFixed(1)}
                          </div>
                          <div className="text-xs text-muted-foreground">Median</div>
                        </div>
                        <div className="text-center p-3 rounded-lg bg-muted/30">
                          <div className="text-lg font-bold text-orange-500">
                            {advancedMetrics.response_time_stats.q3.toFixed(1)}
                          </div>
                          <div className="text-xs text-muted-foreground">Q3</div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Fifth Row - Lead Quality Scatter Plot and Hourly Pattern Heatmap */}
              <div className="grid lg:grid-cols-2 gap-4">
                {/* Lead Quality Scatter Plot */}
                <Card className="glass-card">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Activity className="h-5 w-5 text-indigo-500" />
                      Lead Quality Distribution
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <ScatterChart 
                          data={advancedMetrics.lead_quality}
                          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted))" />
                          <XAxis 
                            type="number" 
                            dataKey="notes_length" 
                            name="Notes Length"
                            stroke="hsl(var(--foreground))"
                            fontSize={12}
                            label={{ value: 'Inquiry Notes Length', position: 'insideBottom', offset: -10, style: { textAnchor: 'middle', fill: 'hsl(var(--foreground))' } }}
                          />
                          <YAxis 
                            type="number" 
                            dataKey="email_completeness" 
                            name="Email Length"
                            stroke="hsl(var(--foreground))"
                            fontSize={12}
                            label={{ value: 'Email Length', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: 'hsl(var(--foreground))' } }}
                          />
                          <Tooltip 
                            cursor={{ strokeDasharray: '3 3' }}
                            content={<CustomTooltip />}
                          />
                          <Scatter 
                            dataKey="quality_score" 
                            name="Quality Score"
                            fill="#6366f1" 
                          />
                        </ScatterChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                {/* Hourly Pattern Heatmap - Represented as Bar Chart */}
                <Card className="glass-card">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Clock className="h-5 w-5 text-pink-500" />
                      Hourly Inquiry Pattern
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <RechartsBarChart 
                          data={advancedMetrics.hourly_pattern.map(item => ({
                            ...item,
                            formattedHour: `${item.hour}:00`
                          }))}
                          margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted))" />
                          <XAxis 
                            dataKey="formattedHour" 
                            stroke="hsl(var(--foreground))"
                            fontSize={12}
                            label={{ value: 'Hour of Day', position: 'insideBottom', offset: -10, style: { textAnchor: 'middle', fill: 'hsl(var(--foreground))' } }}
                          />
                          <YAxis 
                            stroke="hsl(var(--foreground))" 
                            fontSize={12}
                            label={{ value: 'Inquiries', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: 'hsl(var(--foreground))' } }}
                          />
                          <Tooltip content={<CustomTooltip />} />
                          <Bar 
                            dataKey="count" 
                            name="Number of Inquiries"
                            fill="#ec4899" 
                            radius={[2, 2, 0, 0]} 
                          />
                        </RechartsBarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {/* System Status and Recent Activity */}
          {/* <div className="grid lg:grid-cols-3 gap-4">
            <Card className="glass-card">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Activity className="h-5 w-5 text-green-500" />
                  System Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 pt-0">
                <div className="flex items-center justify-between">
                  <span className="text-sm">AI Processing</span>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
                    <span className="text-sm text-green-500">Active</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Lead Scoring</span>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
                    <span className="text-sm text-green-500">Active</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Handoff Queue</span>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 bg-yellow-500 rounded-full animate-pulse" />
                    <span className="text-sm text-yellow-500">Busy</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2 glass-card">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Recent Activity</CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="space-y-3">
                  {recentActivity.map((activity, index) => (
                    <div key={index} className="flex items-start gap-3 p-2 rounded-lg bg-muted/30">
                      <activity.icon className={`h-4 w-4 mt-0.5 ${activity.color} flex-shrink-0`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm leading-relaxed">{activity.message}</p>
                        <p className="text-xs text-muted-foreground mt-1">{activity.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div> */}
        </div>
      </div>
    </LayoutWrapper>
  )
}
