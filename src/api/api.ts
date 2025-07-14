/**
 * Module API cơ sở sử dụng Axios
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from "axios";
import { API_BASE_URL, API_CONFIG, ENDPOINTS } from "./constants.js";

/**
 * Lớp API cơ sở sử dụng Axios
 */
export class ApiClient {
  private axiosInstance: AxiosInstance;

  constructor(baseUrl: string = API_BASE_URL) {
    // Khởi tạo Axios instance với cấu hình cơ bản
    this.axiosInstance = axios.create({
      baseURL: baseUrl,
      timeout: API_CONFIG.TIMEOUT,
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json"
      }
    });

    // Thêm interceptor xử lý lỗi
    this.axiosInstance.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error: any) => {
        if (error.response) {
          console.error(`Lỗi API: ${error.response.status} ${error.response.statusText}`);
        } else if (error.request) {
          console.error("Lỗi kết nối: Không nhận được phản hồi");
        } else {
          console.error(`Lỗi: ${error.message}`);
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Thực hiện yêu cầu GET
   * @param endpoint Endpoint API
   * @param params Tham số truy vấn
   * @returns Dữ liệu phản hồi
   */
  async get<T>(
    endpoint: string,
    params: Record<string, string> = {}
  ): Promise<T> {
    try {
      const response = await this.axiosInstance.get<T>(endpoint, { params });
      return response.data;
    } catch (error) {
      console.error(`Lỗi khi gọi GET ${endpoint}:`, error);
      throw error;
    }
  }

  /**
   * Thực hiện yêu cầu POST
   * @param endpoint Endpoint API
   * @param data Dữ liệu gửi đi
   * @returns Dữ liệu phản hồi
   */
  async post<T>(endpoint: string, data: any): Promise<T> {
    try {
      const response = await this.axiosInstance.post<T>(endpoint, data);
      return response.data;
    } catch (error) {
      console.error(`Lỗi khi gọi POST ${endpoint}:`, error);
      throw error;
    }
  }

  /**
   * Thực hiện yêu cầu PUT
   * @param endpoint Endpoint API
   * @param data Dữ liệu gửi đi
   * @returns Dữ liệu phản hồi
   */
  async put<T>(endpoint: string, data: any): Promise<T> {
    try {
      const response = await this.axiosInstance.put<T>(endpoint, data);
      return response.data;
    } catch (error) {
      console.error(`Lỗi khi gọi PUT ${endpoint}:`, error);
      throw error;
    }
  }

  /**
   * Thực hiện yêu cầu DELETE
   * @param endpoint Endpoint API
   * @param params Tham số truy vấn (tùy chọn)
   * @returns Dữ liệu phản hồi
   */
  async delete<T>(endpoint: string, params: Record<string, string> = {}): Promise<T> {
    try {
      const response = await this.axiosInstance.delete<T>(endpoint, { params });
      return response.data;
    } catch (error) {
      console.error(`Lỗi khi gọi DELETE ${endpoint}:`, error);
      throw error;
    }
  }
  
  /**
   * Thực hiện yêu cầu PATCH
   * @param endpoint Endpoint API
   * @param data Dữ liệu gửi đi
   * @returns Dữ liệu phản hồi
   */
  async patch<T>(endpoint: string, data: any): Promise<T> {
    try {
      const response = await this.axiosInstance.patch<T>(endpoint, data);
      return response.data;
    } catch (error) {
      console.error(`Lỗi khi gọi PATCH ${endpoint}:`, error);
      throw error;
    }
  }
}
