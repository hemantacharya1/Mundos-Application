import React, { useState } from 'react';
import { uploadLeads } from '../api';

export const LeadUpload = ({ onUploadSuccess }) => {
    const [file, setFile] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [message, setMessage] = useState('');

    const handleFileChange = (event) => {
        setFile(event.target.files[0]);
        setMessage('');
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!file) {
            setMessage('Please select a file to upload.');
            return;
        }
        setIsUploading(true);
        setMessage('Uploading...');
        try {
            const response = await uploadLeads(file);
            setMessage(`${response.data.length} new leads processed successfully!`);
            onUploadSuccess(); // Refresh the dashboard
        } catch (error) {
            setMessage(`Upload failed: ${error.response?.data?.detail || error.message}`);
        } finally {
            setIsUploading(false);
            setFile(null);
            event.target.reset();
        }
    };

    return (
        <div className="upload-container">
            <h2>Upload New Leads</h2>
            <form onSubmit={handleSubmit}>
                <input type="file" accept=".csv" onChange={handleFileChange} disabled={isUploading} />
                <button type="submit" disabled={isUploading}>
                    {isUploading ? 'Uploading...' : 'Upload CSV'}
                </button>
            </form>
            {message && <p>{message}</p>}
        </div>
    );
};