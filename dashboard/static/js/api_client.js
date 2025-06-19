/**
 * Temperature Monitoring System API Client
 * Handles communication with the backend API
 */
class APIClient {
    constructor() {
        this.baseUrl = '/api'; // This will be proxied through Flask to your real API
    }
    
    /**
     * Make an API request
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Request options
     * @returns {Promise} - Promise with response data
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
        // Default options
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            credentials: 'same-origin'
        };
        
        // Merge options
        const requestOptions = { ...defaultOptions, ...options };
        
        try {
            console.log(`Making API request to: ${url}`);
            const response = await fetch(url, requestOptions);
            
            // Check if response is JSON
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                
                // Handle API errors
                if (!response.ok) {
                    console.error('API error:', data);
                    throw new Error(data.error || 'API request failed');
                }
                
                return data;
            } else {
                // Handle non-JSON responses
                if (!response.ok) {
                    throw new Error('API request failed');
                }
                
                return await response.text();
            }
        } catch (error) {
            console.error('API request error:', error);
            throw error;
        }
    }
    
    // Temperature Endpoints
    async getTemperatures(params = {}) {
        // Clean up params - remove undefined values
        Object.keys(params).forEach(key => 
            params[key] === undefined && delete params[key]
        );
        const queryParams = new URLSearchParams(params).toString();
        return this.request(`/temperatures?${queryParams}`);
    }
    
    async getLatestTemperatures(params = {}) {
        // Clean up params - remove undefined values
        Object.keys(params).forEach(key => 
            params[key] === undefined && delete params[key]
        );
        const queryParams = new URLSearchParams(params).toString();
        return this.request(`/temperatures/latest?${queryParams}`);
    }
    
    async getTemperatureStats(params = {}) {
        // Clean up params - remove undefined values
        Object.keys(params).forEach(key => 
            params[key] === undefined && delete params[key]
        );
        const queryParams = new URLSearchParams(params).toString();
        return this.request(`/temperatures/statistics?${queryParams}`);
    }
    
    async getTemperatureAlerts(params = {}) {
        // Clean up params - remove undefined values
        Object.keys(params).forEach(key => 
            params[key] === undefined && delete params[key]
        );
        const queryParams = new URLSearchParams(params).toString();
        return this.request(`/temperatures/alerts?${queryParams}`);
    }
    
    // Customer Endpoints
    async getCurrentCustomer() {
        return this.request('/customers/me');
    }
    
    async getCustomerFacilities() {
        return this.request('/customers/me/facilities');
    }
    
    async triggerIngestion() {
        return this.request('/customers/me/trigger-ingestion', {
            method: 'POST'
        });
    }
    
    // Admin Endpoints
    async getAllCustomers() {
        return this.request('/admin/customers');
    }
    
    async getSystemOverview() {
        return this.request('/admin/system/overview');
    }
    
    async getSystemAlerts() {
        return this.request('/admin/system/alerts');
    }
}

// Create global API client instance
const apiClient = new APIClient();