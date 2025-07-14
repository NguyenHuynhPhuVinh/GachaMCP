/**
 * Module công cụ ví dụ
 */

/**
 * Lấy thông tin ví dụ
 * @param id ID của mục
 * @returns Thông tin ví dụ
 */
export async function getExample(id: number) {
  try {
    // Mô phỏng gọi API
    return {
      id,
      name: `Ví dụ ${id}`,
      description: 'Đây là một mục ví dụ',
      createdAt: new Date().toISOString(),
    };
  } catch (error: unknown) {
    console.error(`Lỗi khi lấy ví dụ: ${(error as Error).message}`);
    throw error;
  }
}

/**
 * Tìm kiếm ví dụ
 * @param query Từ khóa tìm kiếm
 * @param limit Giới hạn kết quả
 * @returns Danh sách kết quả
 */
export async function searchExamples(query: string, limit: number = 10) {
  try {
    // Mô phỏng tìm kiếm
    return Array.from({ length: limit }, (_, i) => ({
      id: i + 1,
      name: `Kết quả ${i + 1} cho "${query}"`,
      relevance: Math.random(),
    })).sort((a, b) => b.relevance - a.relevance);
  } catch (error: unknown) {
    console.error(`Lỗi khi tìm kiếm: ${(error as Error).message}`);
    throw error;
  }
}
