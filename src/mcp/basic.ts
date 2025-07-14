/**
 * Module đăng ký công cụ MCP cơ bản
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

/**
 * Đăng ký các công cụ MCP cơ bản
 * @param server Server MCP
 */
export function registerBasicTools(server: McpServer) {
  // Đăng ký công cụ hello
  server.tool("hello", "Trả về lời chào đơn giản", {}, async () => {
    return {
      content: [
        {
          type: "text",
          text: "Xin chào từ MCP Server!",
        },
      ],
    };
  });

  // Đăng ký công cụ greet
  server.tool(
    "greet",
    "Chào một người cụ thể",
    {
      name: z.string().describe("Tên người muốn chào"),
    },
    async ({ name }) => {
      return {
        content: [
          {
            type: "text",
            text: `Xin chào ${name}!`,
          },
        ],
      };
    }
  );

  // Đăng ký công cụ giới thiệu
  server.tool("introduction", "Giới thiệu về MCP Server", {}, async () => {
    return {
      content: [
        {
          type: "text",
          text: `# MCP Server

MCP Server là một Model Context Protocol (MCP) server đơn giản.

## Các công cụ có sẵn

- **hello**: Trả về lời chào đơn giản
- **greet**: Chào một người cụ thể
- **getExample**: Lấy thông tin về một mục ví dụ cụ thể
- **searchExamples**: Tìm kiếm các mục ví dụ

## Tài nguyên có sẵn

- **documentation**: Tài liệu hướng dẫn sử dụng`,
        },
      ],
    };
  });
}
