import React from 'react';
import { updateLeadStatus } from '../api';

export const LeadList = ({ title, leads, onStatusChange }) => {
    const handleUpdateStatus = async (leadId, newStatus) => {
        try {
            await updateLeadStatus(leadId, newStatus);
            onStatusChange(); // Refresh the dashboard
        } catch (error) {
            console.error(`Failed to update status for lead ${leadId}:`, error);
            alert('Failed to update lead status.');
        }
    };

    return (
        <div className="lead-list">
            <h3>{title} ({leads.length})</h3>
            {leads.length === 0 ? (
                <p>No leads in this queue.</p>
            ) : (
                leads.map((lead) => (
                    <div key={lead.id} className="lead-card">
                        <h4>{lead.first_name} {lead.last_name}</h4>
                        <p><strong>Email:</strong> {lead.email}</p>
                        <p><strong>Phone:</strong> {lead.phone_number || 'N/A'}</p>
                        <p><strong>Original Inquiry:</strong> {lead.inquiry_notes}</p>
                        
                        {/* --- NEW DYNAMIC SECTION --- */}
                        {lead.ai_summary && (
                            <div className="ai-insights">
                                <p><strong>AI Summary of Reply:</strong> {lead.ai_summary}</p>
                                {lead.ai_drafted_reply && (
                                    <div className="drafted-reply">
                                        <strong>AI Drafted Reply:</strong>
                                        <textarea readOnly defaultValue={lead.ai_drafted_reply}></textarea>
                                    </div>
                                )}
                            </div>
                        )}
                        {/* --- END NEW SECTION --- */}

                        <div className="lead-actions">
                            <button onClick={() => handleUpdateStatus(lead.id, 'converted')}>Mark Converted</button>
                            <button onClick={() => handleUpdateStatus(lead.id, 'archived_not_interested')}>Archive</button>
                        </div>
                    </div>
                ))
            )}
        </div>
    );
};