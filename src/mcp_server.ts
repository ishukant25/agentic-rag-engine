/**
 * Model Context Protocol (MCP) Server
 * Implements JSON-RPC 2.0 over standard I/O (Stdio)
 * Author: Ishukant (https://github.com/ishukant25)
 */

import readline from 'readline';
import { HERMES_MCP_TOOLS, executeToolCall } from './hermes_agent';

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false,
});

function send(response: any) {
    process.stdout.write(JSON.stringify(response) + '\n');
}

rl.on('line', async (line) => {
    if (!line.trim()) return;

    let req: any;
    try {
        req = JSON.parse(line);
    } catch {
        return;
    }

    const { id, method, params } = req;

    try {
        switch (method) {
            case 'initialize': {
                send({
                    jsonrpc: '2.0',
                    id,
                    result: {
                        protocolVersion: '2024-11-05',
                        capabilities: { tools: {} },
                        serverInfo: {
                            name: 'agentic-mcp-server',
                            version: '1.0.0',
                        },
                    },
                });
                break;
            }

            case 'tools/list': {
                send({
                    jsonrpc: '2.0',
                    id,
                    result: { tools: HERMES_MCP_TOOLS.map(t => t.function) },
                });
                break;
            }

            case 'tools/call': {
                const { name, arguments: args } = params;
                const result = await executeToolCall(name, args || {});
                send({
                    jsonrpc: '2.0',
                    id,
                    result: { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] },
                });
                break;
            }

            default:
                send({
                    jsonrpc: '2.0',
                    id,
                    error: { code: -32601, message: `Method not found: ${method}` },
                });
        }
    } catch (err: any) {
        send({
            jsonrpc: '2.0',
            id,
            error: { code: -32603, message: err?.message || 'Internal MCP Error' },
        });
    }
});
