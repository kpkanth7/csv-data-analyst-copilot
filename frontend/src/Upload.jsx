import { useState } from 'react';

function Upload({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile);
      setError('');
    } else {
      setFile(null);
      setError("I only take .csv files.");
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Sending it over to the FastAPI backend
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      // Passing the session ID back to the main app so we can start chatting
      onUploadSuccess(data.session_id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h1>CSV Data Analyst Copilot</h1>
      <p>Drop your CSV file here to start exploring your data.</p>
      
      <div className={`upload-zone ${file ? 'active' : ''}`} onClick={() => document.getElementById('csvUpload').click()}>
        <div className="upload-icon">📁</div>
        {file ? (
          <p><strong>{file.name}</strong> ready to go.</p>
        ) : (
          <p>Click to select or drag and drop a .csv file</p>
        )}
        <input 
          id="csvUpload" 
          type="file" 
          accept=".csv" 
          className="file-input" 
          onChange={handleFileChange} 
        />
      </div>

      {error && <div className="error-message">{error}</div>}

      <div style={{ marginTop: '2rem' }}>
        <button 
          className="btn" 
          onClick={handleUpload} 
          disabled={!file || loading}
        >
          {loading ? 'Analyzing...' : 'Start Analysis'}
        </button>
      </div>
    </div>
  );
}

export default Upload;
