import React, { useState, useEffect, useCallback } from 'react';
import { getLeadsByStatus } from '../api';
import { LeadUpload } from './LeadUpload';
import { LeadList } from './LeadList';

export const Dashboard = () => {
    const [urgentLeads, setUrgentLeads] = useState([]);
    const [respondedLeads, setRespondedLeads] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    const fetchLeads = useCallback(async () => {
        setIsLoading(true);
        try {
            const urgentPromise = getLeadsByStatus('needs_immediate_attention');
            const respondedPromise = getLeadsByStatus('responded');
            
            const [urgentResponse, respondedResponse] = await Promise.all([urgentPromise, respondedPromise]);
            
            setUrgentLeads(urgentResponse.data);
            setRespondedLeads(respondedResponse.data);
        } catch (error) {
            console.error("Failed to fetch leads:", error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchLeads();
    }, [fetchLeads]);

    return (
        <div className="dashboard">
            <LeadUpload onUploadSuccess={fetchLeads} />
            <hr />
            <div className="queues-container">
                {isLoading ? (
                    <p>Loading agent queues...</p>
                ) : (
                    <>
                        <LeadList title="Needs Immediate Attention" leads={urgentLeads} onStatusChange={fetchLeads} />
                        <LeadList title="Responded - Needs Review" leads={respondedLeads} onStatusChange={fetchLeads} />
                    </>
                )}
            </div>
        </div>
    );
};