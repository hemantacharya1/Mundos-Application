import { useState, useEffect } from 'react';
import { apiService, Lead, Communication } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface UseConversationReturn {
  lead: Lead | null;
  communications: Communication[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  refreshData: () => Promise<void>;
}

export function useConversation(leadId: string): UseConversationReturn {
  const [lead, setLead] = useState<Lead | null>(null);
  const [communications, setCommunications] = useState<Communication[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const fetchData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Fetch lead data and communications in parallel
      const [leadData, commsData] = await Promise.all([
        apiService.getLead(leadId),
        apiService.getLeadCommunications(leadId)
      ]);
      
      setLead(leadData);
      setCommunications(commsData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch conversation data';
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (leadId) {
      fetchData();
    }
  }, [leadId]);

  const sendMessage = async (content: string) => {
    if (!lead || !content.trim()) return;
    
    try {
      await apiService.sendManualReply(lead.id, content);
      
      // Add the new message to the communications list
      const newComm: Communication = {
        id: `temp-${Date.now()}`, // Temporary ID for optimistic update
        lead_id: lead.id,
        type: 'email',
        direction: 'outgoing_manual',
        content: content,
        sent_at: new Date().toISOString()
      };
      
      setCommunications(prev => [...prev, newComm]);
      
      toast({
        title: "Message sent",
        description: "Your reply has been sent successfully.",
      });
      
      // Refresh data to get the actual communication record
      await fetchData();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const refreshData = async () => {
    await fetchData();
  };

  return {
    lead,
    communications,
    isLoading,
    error,
    sendMessage,
    refreshData,
  };
} 