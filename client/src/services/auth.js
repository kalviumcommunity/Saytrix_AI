class AuthService {
  constructor() {
    this.baseURL = 'http://localhost:5000';
    this.token = localStorage.getItem('saytrix_token');
  }

  async register(email, password, name) {
    try {
      const response = await fetch(`${this.baseURL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password, name }),
      });

      const data = await response.json();
      
      if (response.ok) {
        this.token = data.token;
        localStorage.setItem('saytrix_token', data.token);
        localStorage.setItem('saytrix_user', JSON.stringify(data.user));
        return { success: true, user: data.user };
      } else {
        return { success: false, error: data.error };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  }

  async login(email, password) {
    try {
      const response = await fetch(`${this.baseURL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();
      
      if (response.ok) {
        this.token = data.token;
        localStorage.setItem('saytrix_token', data.token);
        localStorage.setItem('saytrix_user', JSON.stringify(data.user));
        return { success: true, user: data.user };
      } else {
        return { success: false, error: data.error };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  }

  logout() {
    this.token = null;
    localStorage.removeItem('saytrix_token');
    localStorage.removeItem('saytrix_user');
  }

  isAuthenticated() {
    return !!this.token;
  }

  getUser() {
    const user = localStorage.getItem('saytrix_user');
    return user ? JSON.parse(user) : null;
  }

  getAuthHeaders() {
    return this.token ? { 'Authorization': `Bearer ${this.token}` } : {};
  }

  async verifyToken() {
    if (!this.token) return false;

    try {
      const response = await fetch(`${this.baseURL}/auth/verify`, {
        headers: this.getAuthHeaders(),
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }
}

export const authService = new AuthService();