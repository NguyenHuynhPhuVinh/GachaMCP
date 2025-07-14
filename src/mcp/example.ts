/**
 * Module đăng ký công cụ MCP ví dụ
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import * as exampleTools from "../tools/example.js";

/**
 * Đăng ký các công cụ MCP ví dụ
 * @param server Server MCP
 */
export function registerExampleTools(server: McpServer) {
  // Đăng ký công cụ lấy ví dụ
  server.tool(
    "getExample",
    "Lấy thông tin về một mục ví dụ cụ thể",
    {
      id: z.number().describe("ID của mục ví dụ"),
    },
    async ({ id }) => {
      try {
        const data = await exampleTools.getExample(id);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      } catch (error: unknown) {
        return {
          content: [
            {
              type: "text",
              text: `Lỗi khi lấy thông tin ví dụ: ${(error as Error).message}`,
            },
          ],
        };
      }
    }
  );

  // Đăng ký công cụ tìm kiếm ví dụ
  server.tool(
    "searchExamples",
    "Tìm kiếm các mục ví dụ",
    {
      query: z.string().describe("Từ khóa tìm kiếm"),
      limit: z.number().optional().describe("Số lượng kết quả tối đa (mặc định: 10)"),
    },
    async ({ query, limit }) => {
      try {
        const data = await exampleTools.searchExamples(query, limit);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      } catch (error: unknown) {
        return {
          content: [
            {
              type: "text",
              text: `Lỗi khi tìm kiếm ví dụ: ${(error as Error).message}`,
            },
          ],
        };
      }
    }
  );
}
