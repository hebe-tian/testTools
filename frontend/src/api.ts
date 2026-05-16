const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

const apiClient = {
  async post<T>(path: string, data: unknown): Promise<T> {
    const url = `${API_BASE_URL}${path}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '请求失败' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
  },
};

export { apiClient };
