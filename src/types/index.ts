/**
 * Các kiểu dữ liệu được sử dụng trong ứng dụng
 */

/**
 * Kiểu dữ liệu cho mục ví dụ
 */
export interface Example {
  id: number;
  name: string;
  description: string;
  createdAt: string;
}

/**
 * Kiểu dữ liệu cho kết quả tìm kiếm ví dụ
 */
export interface SearchResult {
  id: number;
  name: string;
  relevance: number;
}

/**
 * Kiểu dữ liệu cho cấu hình API
 */
export interface ApiConfig {
  baseUrl: string;
  timeout: number;
  retryCount: number;
  retryDelay: number;
}
