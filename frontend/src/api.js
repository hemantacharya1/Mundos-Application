import axios from 'axios';

const apiClient = axios.create({
    baseURL: 'http://127.0.0.1:8000/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

export const uploadLeads = (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/leads/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
};

export const getLeadsByStatus = (status) => {
    return apiClient.get(`/leads?status=${status}`);
};

export const updateLeadStatus = (leadId, status) => {
    // The status needs to be sent as a plain string in the body
    return apiClient.put(`/leads/${leadId}/status`, `"${status}"`, {
        headers: {
            'Content-Type': 'application/json',
        },
    });
};