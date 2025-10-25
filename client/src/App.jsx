import React, { useState, useEffect } from 'react';
import { Upload, Search, AlertCircle, CheckCircle, FileText, Loader2, X, File, User, Calendar } from 'lucide-react';

function App() {
  const [file, setFile] = useState(null);
  const [isUploaded, setIsUploaded] = useState(false);
  const [uploadInfo, setUploadInfo] = useState(null);
  const [searchType, setSearchType] = useState('serial'); // 'serial' or 'retailer'
  const [startSerial, setStartSerial] = useState('');
  const [endSerial, setEndSerial] = useState('');
  const [retailerMsisdn, setRetailerMsisdn] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [uploadLoading, setUploadLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/status`);
      const data = await response.json();
      if (data.loaded) {
        setIsUploaded(true);
        setUploadInfo({ rows: data.rows });
      }
    } catch (err) {
      console.error('Error checking status:', err);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      validateAndSetFile(selectedFile);
    }
  };

  const validateAndSetFile = (selectedFile) => {
    const validTypes = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel'];
    const maxSize = 16 * 1024 * 1024;

    if (!validTypes.includes(selectedFile.type) &&
        !selectedFile.name.endsWith('.xlsx') &&
        !selectedFile.name.endsWith('.xls')) {
      setError('Invalid file type. Please upload .xlsx or .xls files only.');
      return;
    }

    if (selectedFile.size > maxSize) {
      setError('File size exceeds 16MB limit.');
      return;
    }

    setFile(selectedFile);
    setError('');
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      validateAndSetFile(droppedFile);
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
    setError('');
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setUploadLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setIsUploaded(true);
        setUploadInfo(data);
        setError('');
        setFile(null);
      } else {
        setError(data.error || 'Upload failed');
      }
    } catch (err) {
      setError('Error uploading file. Make sure Flask server is running on port 5000.');
    } finally {
      setUploadLoading(false);
    }
  };

  const handleFilter = async () => {
    if (searchType === 'serial') {
      if (!startSerial || !endSerial) {
        setError('Please enter both start and end serial numbers');
        return;
      }
    } else {
      if (!retailerMsisdn) {
        setError('Please enter retailer MSISDN');
        return;
      }
    }

    if (!isUploaded) {
      setError('Please upload an Excel file first');
      return;
    }

    setLoading(true);
    setError('');
    setResults(null);

    try {
      let endpoint = searchType === 'serial' ? `${API_URL}/filter` : `${API_URL}/filter-retailer`;
      let body = searchType === 'serial'
        ? {
            start_serial: startSerial,
            end_serial: endSerial,
            start_date: startDate || null,
            end_date: endDate || null
          }
        : {
            retailer_msisdn: retailerMsisdn,
            start_date: startDate || null,
            end_date: endDate || null
          };

      console.log('Sending request to:', endpoint);
      console.log('Request body:', body);

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      console.log('Response status:', response.status);
      const data = await response.json();
      console.log('Response data:', data);

      if (response.ok && !data.error) {
        setResults(data);
        console.log('Results set successfully:', data);
      } else {
        setError(data.error || 'Filter failed');
        console.error('Filter error:', data);
      }
    } catch (err) {
      console.error('Fetch error:', err);
      setError(`Error filtering serials: ${err.message}. Make sure Flask server is running on port 5000.`);
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-5xl mx-auto">
        <div className="bg-white rounded-lg shadow-xl p-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Serial Number Filter</h1>
          <p className="text-gray-600 mb-8">Upload Excel file and filter activated serials by range or retailer</p>

          {/* Upload Section */}
          <div className="mb-8">
            <div className="flex items-center gap-4 mb-4">
              <Upload className="w-8 h-8 text-indigo-600" />
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-gray-800 mb-1">Upload Excel File</h2>
                <p className="text-sm text-gray-600">Upload your monthly serial numbers Excel file (.xlsx, .xls)</p>
              </div>
            </div>

            {/* Drag and Drop Zone */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`p-8 border-2 border-dashed rounded-lg transition-all ${
                isDragging
                  ? 'border-indigo-500 bg-indigo-50'
                  : 'border-gray-300 bg-gray-50'
              }`}
            >
              {!file ? (
                <div className="text-center">
                  <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-700 font-medium mb-2">
                    Drag and drop your Excel file here
                  </p>
                  <p className="text-gray-500 text-sm mb-4">or</p>
                  <label className="inline-flex items-center px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 cursor-pointer transition-colors">
                    <Upload className="w-5 h-5 mr-2" />
                    Browse Files
                    <input
                      type="file"
                      accept=".xlsx,.xls"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                  </label>
                  <p className="text-xs text-gray-500 mt-4">
                    Supported formats: .xlsx, .xls (Max size: 16MB)
                  </p>
                </div>
              ) : (
                <div className="flex items-center justify-between bg-white p-4 rounded-lg border border-gray-200">
                  <div className="flex items-center gap-3 flex-1">
                    <div className="p-2 bg-indigo-100 rounded">
                      <File className="w-6 h-6 text-indigo-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-800 truncate">{file.name}</p>
                      <p className="text-sm text-gray-500">{formatFileSize(file.size)}</p>
                    </div>
                  </div>
                  <button
                    onClick={handleRemoveFile}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5 text-gray-500" />
                  </button>
                </div>
              )}
            </div>

            {file && (
              <div className="mt-4">
                <button
                  onClick={handleUpload}
                  disabled={uploadLoading}
                  className="w-full px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors font-medium"
                >
                  {uploadLoading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="w-5 h-5" />
                      Upload File
                    </>
                  )}
                </button>
              </div>
            )}

            {isUploaded && uploadInfo && (
              <div className="mt-4 flex items-center gap-2 text-green-700 bg-green-50 p-4 rounded-lg border border-green-200">
                <CheckCircle className="w-5 h-5 flex-shrink-0" />
                <div>
                  <p className="font-medium">File uploaded successfully!</p>
                  <p className="text-sm">{uploadInfo.rows} rows loaded from Excel file</p>
                </div>
              </div>
            )}
          </div>

          {/* Search Type Selector */}
          <div className="mb-6">
            <div className="flex gap-4 mb-4">
              <button
                onClick={() => setSearchType('serial')}
                className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
                  searchType === 'serial'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <Search className="w-5 h-5" />
                Search by Serial Range
              </button>
              <button
                onClick={() => setSearchType('retailer')}
                className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
                  searchType === 'retailer'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <User className="w-5 h-5" />
                Search by Retailer
              </button>
            </div>
          </div>

          {/* Filter Section */}
          <div className="mb-8">
            <div className="flex items-center gap-4 mb-4">
              {searchType === 'serial' ? (
                <>
                  <Search className="w-8 h-8 text-indigo-600" />
                  <h2 className="text-xl font-semibold text-gray-800">Filter by Serial Range</h2>
                </>
              ) : (
                <>
                  <User className="w-8 h-8 text-indigo-600" />
                  <h2 className="text-xl font-semibold text-gray-800">Filter by Retailer MSISDN</h2>
                </>
              )}
            </div>

            {searchType === 'serial' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Start Serial Number</label>
                  <input
                    type="text"
                    value={startSerial}
                    onChange={(e) => setStartSerial(e.target.value)}
                    placeholder="8925403506100176553"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">Enter only the numeric part (without "SERIAL_" prefix)</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">End Serial Number</label>
                  <input
                    type="text"
                    value={endSerial}
                    onChange={(e) => setEndSerial(e.target.value)}
                    placeholder="8925403506100176800"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">Enter only the numeric part (without "SERIAL_" prefix)</p>
                </div>
              </div>
            ) : (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Retailer MSISDN</label>
                <input
                  type="text"
                  value={retailerMsisdn}
                  onChange={(e) => setRetailerMsisdn(e.target.value)}
                  placeholder="Enter retailer MSISDN"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
            )}

            {/* Date Filter Section */}
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <div className="flex items-center gap-2 mb-3">
                <Calendar className="w-5 h-5 text-indigo-600" />
                <h3 className="font-medium text-gray-800">Date Filter (Optional)</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            <button
              onClick={handleFilter}
              disabled={loading || !isUploaded}
              className="w-full px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors font-medium"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Filtering...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  Filter {searchType === 'serial' ? 'Serials' : 'by Retailer'}
                </>
              )}
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 flex items-start gap-3 text-red-700 bg-red-50 p-4 rounded-lg border border-red-200">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Results Section */}
          {results && (
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-6 border border-indigo-200">
              <div className="flex items-center gap-3 mb-6">
                <FileText className="w-7 h-7 text-indigo-600" />
                <h2 className="text-2xl font-semibold text-gray-800">Results</h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-white rounded-lg p-4 shadow-sm">
                  <p className="text-sm text-gray-600 mb-1">
                    {searchType === 'serial' ? 'Total in Range' : 'Total for Retailer'}
                  </p>
                  <p className="text-3xl font-bold text-indigo-600">
                    {results.total_in_range || results.total_count}
                  </p>
                </div>
                <div className="bg-white rounded-lg p-4 shadow-sm">
                  <p className="text-sm text-gray-600 mb-1">Activated Serials</p>
                  <p className="text-3xl font-bold text-green-600">{results.activated_count}</p>
                </div>
                <div className="bg-white rounded-lg p-4 shadow-sm">
                  <p className="text-sm text-gray-600 mb-1">Activation Rate</p>
                  <p className="text-3xl font-bold text-purple-600">{results.activation_rate}%</p>
                </div>
              </div>

              {results.activated_serials && results.activated_serials.length > 0 && (
                <div className="bg-white rounded-lg p-4 shadow-sm">
                  <h3 className="font-semibold text-gray-800 mb-3">
                    Activated Serials (First 100)
                    {results.has_date_column && (
                      <span className="text-sm font-normal text-gray-600 ml-2">
                        - Date column: {results.date_column_name}
                      </span>
                    )}
                  </h3>
                  <div className="max-h-96 overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          {Object.keys(results.activated_serials[0]).map((key, idx) => (
                            <th key={idx} className="px-4 py-2 text-left font-medium text-gray-700 capitalize">
                              {key.replace(/_/g, ' ')}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {results.activated_serials.map((serial, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            {Object.values(serial).map((value, valIdx) => (
                              <td key={valIdx} className="px-4 py-2">
                                {value !== null && value !== undefined ? String(value) : '-'}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {results.activated_serials.length === 100 && (
                    <p className="text-xs text-gray-500 mt-3 text-center">
                      Showing first 100 results. Download full report for complete data.
                    </p>
                  )}
                </div>
              )}

              {results.activated_serials && results.activated_serials.length === 0 && (
                <div className="bg-white rounded-lg p-8 text-center">
                  <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600">No activated serials found for the given criteria.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;