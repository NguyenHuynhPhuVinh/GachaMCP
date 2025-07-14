/**
 * Cấu hình ứng dụng
 */

/**
 * Cấu hình môi trường
 */
export const ENV = {
  // Môi trường thực thi (development, production, test)
  NODE_ENV: process.env.NODE_ENV || "development",

  // Cổng máy chủ (nếu cần)
  PORT: process.env.PORT || 3000,

  // Cờ gỡ lỗi
  DEBUG: process.env.DEBUG === "true",
};

/**
 * Cấu hình ứng dụng
 */
export const APP_CONFIG = {
  // Tên ứng dụng
  NAME: "MCP Server",

  // Phiên bản
  VERSION: "1.0.0",

  // Thời gian chờ mặc định (ms)
  DEFAULT_TIMEOUT: 5000,

  // Số lần thử lại tối đa
  MAX_RETRIES: 3,
};

/**
 * Cấu hình ghi log
 */
export const LOG_CONFIG = {
  // Cấp độ ghi log (debug, info, warn, error)
  LEVEL: process.env.LOG_LEVEL || "info",

  // Có ghi log vào tệp không
  FILE_LOGGING: process.env.FILE_LOGGING === "true",

  // Đường dẫn tệp ghi log
  LOG_FILE_PATH: process.env.LOG_FILE_PATH || "./logs/app.log",
};
