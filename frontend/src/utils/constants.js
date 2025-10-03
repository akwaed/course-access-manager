export const UK_COLORS = {
  wildcatBlue: '#0033A0',
  bluegrass: '#1E8AFF',
  midnight: '#1B365D',
  sky: '#B1C9E8',
  white: '#FFFFFF',
  goldenrod: '#FFDC00',
  sunset: '#FFA360',
  riverGreen: '#4CBCC0',
  coolNeutral: '#DCDDDE',
  warmNeutral: '#D6D2C4',
  black: '#000000'
};

export const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';

export const USER_ROLES = {
  SYSTEM_ADMIN: 'System Admin',
  COLLEGE_PRIMARY: 'College Primary Contact',
  DEPARTMENT: 'Department Contact'
};

export const CONTACT_TYPES = {
  COLLEGE: 'College',
  DEPARTMENT: 'Department',
  COURSE: 'Course Coordinator'
};

export const LEVEL_TYPES = {
  REPORT: 'Report Viewer',
  SOURCE: 'Source Viewer'
};

// ===========================
// File: frontend/src/services/api.js
// ===========================
import { API_BASE_URL } from '../utils/constants';

class ApiService {
  constructor() {
    this.baseUrl = API_BASE_URL;
    this.token = localStorage.getItem('auth_token');
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    if (this.token) {
      config.headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Contacts
  async getContacts() {
    return this.request('/api/contacts');
  }

  async addContact(contact) {
    return this.request('/api/contacts', {
      method: 'POST',
      body: JSON.stringify(contact),
    });
  }

  async updateContact(id, contact) {
    return this.request(`/api/contacts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(contact),
    });
  }

  async deleteContact(id) {
    return this.request(`/api/contacts/${id}`, {
      method: 'DELETE',
    });
  }

  // Courses
  async getCourses() {
    return this.request('/api/courses');
  }

  async getHierarchy() {
    return this.request('/api/hierarchy');
  }

  // Export
  async exportData(options = {}) {
    const response = await fetch(`${this.baseUrl}/api/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(options),
    });

    if (!response.ok) {
      throw new Error('Export failed');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    const date = new Date().toISOString().split('T')[0];
    a.href = url;
    a.download = `ReportViewer-${date}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  // Pending Changes
  async getPendingChanges() {
    return this.request('/api/pending-changes');
  }

  async approvePendingChange(id, reviewer) {
    return this.request(`/api/pending-changes/${id}/approve`, {
      method: 'PUT',
      body: JSON.stringify({ reviewer }),
    });
  }

  // Auth
  async login(email, password) {
    const response = await this.request('/api/auth/login', {
      method: 'POST',
      headers: {
        'Authorization': 'Basic ' + btoa(`${email}:${password}`),
      },
    });
    
    if (response.token) {
      this.token = response.token;
      localStorage.setItem('auth_token', response.token);
    }
    
    return response;
  }

  logout() {
    this.token = null;
    localStorage.removeItem('auth_token');
  }
}

export default new ApiService();
