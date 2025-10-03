import apiService from './api';

class AuthService {
  constructor() {
    this.user = this.loadUser();
  }

  loadUser() {
    const userData = localStorage.getItem('user_data');
    return userData ? JSON.parse(userData) : null;
  }

  saveUser(user) {
    localStorage.setItem('user_data', JSON.stringify(user));
    this.user = user;
  }

  async login(email, password) {
    try {
      const response = await apiService.login(email, password);
      this.saveUser(response);
      return response;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }

  logout() {
    localStorage.removeItem('user_data');
    this.user = null;
    apiService.logout();
  }

  getCurrentUser() {
    return this.user;
  }

  isAuthenticated() {
    return !!this.user;
  }

  hasRole(role) {
    return this.user && this.user.role === role;
  }

  isSystemAdmin() {
    return this.hasRole('System Admin') || this.user?.email === 'admin@uky.edu';
  }
}

export default new AuthService();