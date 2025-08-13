import { Lead, Communication } from './api';

export function formatLeadName(lead: Lead): string {
  if (lead.first_name && lead.last_name) {
    return `${lead.first_name} ${lead.last_name}`;
  } else if (lead.first_name) {
    return lead.first_name;
  } else if (lead.last_name) {
    return lead.last_name;
  } else {
    return lead.email.split('@')[0];
  }
}

export function formatCompanyName(lead: Lead): string {
  if (lead.inquiry_notes) {
    const companyMatch = lead.inquiry_notes.match(/company[:\s]+([^\n,]+)/i);
    if (companyMatch) {
      return companyMatch[1].trim();
    }
  }
  
  const domain = lead.email.split('@')[1];
  if (domain) {
    return domain.split('.')[0].charAt(0).toUpperCase() + 
           domain.split('.')[0].slice(1) + ' Solutions';
  }
  
  return 'Unknown Company';
}

export function calculateUrgencyScore(lead: Lead): number {
  let score = 0;
  
  switch (lead.status) {
    case 'needs_immediate_attention':
      score += 40;
      break;
    case 'new':
      score += 30;
      break;
    case 'nurturing':
      score += 20;
      break;
    case 'responded':
      score += 10;
      break;
    default:
      score += 5;
  }
  
  if (lead.nurture_attempts > 3) {
    score += 25;
  } else if (lead.nurture_attempts > 1) {
    score += 15;
  }
  
  if (lead.inquiry_notes && lead.inquiry_notes.length > 100) {
    score += 20;
  } else if (lead.inquiry_notes && lead.inquiry_notes.length > 50) {
    score += 10;
  }
  
  return Math.min(score, 100);
}

export function getStatusDisplayInfo(status: string) {
  switch (status) {
    case 'new':
      return {
        label: 'New',
        color: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
        priority: 'High'
      };
    case 'needs_immediate_attention':
      return {
        label: 'Urgent',
        color: 'bg-red-500/10 text-red-500 border-red-500/20',
        priority: 'Critical'
      };
    case 'nurturing':
      return {
        label: 'In Progress',
        color: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
        priority: 'Medium'
      };
    case 'responded':
      return {
        label: 'Qualified',
        color: 'bg-green-500/10 text-green-500 border-green-500/20',
        priority: 'High'
      };
    case 'converted':
      return {
        label: 'Converted',
        color: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
        priority: 'Low'
      };
    default:
      return {
        label: status.charAt(0).toUpperCase() + status.slice(1).replace(/_/g, ' '),
        color: 'bg-gray-500/10 text-gray-500 border-gray-500/20',
        priority: 'Medium'
      };
  }
}

export function getPriorityColor(priority: string) {
  switch (priority) {
    case 'Critical':
      return 'bg-red-500/10 text-red-500 border-red-500/20';
    case 'High':
      return 'bg-orange-500/10 text-orange-500 border-orange-500/20';
    case 'Medium':
      return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
    case 'Low':
      return 'bg-green-500/10 text-green-500 border-green-500/20';
    default:
      return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
  }
}

export function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInMs = now.getTime() - date.getTime();
  const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
  const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

  if (diffInMinutes < 1) return 'Just now';
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
  if (diffInHours < 24) return `${diffInHours}h ago`;
  if (diffInDays < 7) return `${diffInDays}d ago`;
  
  return date.toLocaleDateString();
}

export function formatWaitingTime(lead: Lead): string {
  const lastComm = lead.updated_at;
  const now = new Date();
  const diffInMs = now.getTime() - new Date(lastComm).getTime();
  const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
  const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));

  if (diffInMinutes < 60) {
    return `${diffInMinutes}m`;
  } else if (diffInHours < 24) {
    return `${diffInHours}h`;
  } else {
    const days = Math.floor(diffInHours / 24);
    return `${days}d`;
  }
} 