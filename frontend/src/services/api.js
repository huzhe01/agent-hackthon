/**
 * GrowEngine API 服务
 * ==================
 * 统一管理所有后端 API 调用
 */

// API 基础地址配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * 通用请求封装
 */
async function request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;

    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
        ...options,
    };

    try {
        const response = await fetch(url, config);

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`Request failed: ${endpoint}`, error);
        throw error;
    }
}

// ==================== 广告计划 API ====================

/**
 * 获取广告计划列表
 */
export async function getCampaigns(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const endpoint = queryString ? `/api/campaigns?${queryString}` : '/api/campaigns';
    return request(endpoint);
}

/**
 * 获取单个广告计划
 */
export async function getCampaign(id) {
    return request(`/api/campaigns/${id}`);
}

/**
 * 创建广告计划
 */
export async function createCampaign(data) {
    return request('/api/campaigns', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

/**
 * 更新广告计划
 */
export async function updateCampaign(id, data) {
    return request(`/api/campaigns/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
    });
}

/**
 * 删除广告计划
 */
export async function deleteCampaign(id) {
    return request(`/api/campaigns/${id}`, {
        method: 'DELETE',
    });
}

/**
 * 切换广告计划状态
 */
export async function toggleCampaignStatus(id) {
    return request(`/api/campaigns/${id}/toggle`, {
        method: 'POST',
    });
}

// ==================== 指标 API ====================

/**
 * 获取实时指标
 */
export async function getRealtimeMetrics() {
    return request('/api/metrics/realtime');
}

/**
 * 获取趋势数据
 */
export async function getMetricsTrend(hours = 24) {
    return request(`/api/metrics/trend?hours=${hours}`);
}

// ==================== Agent Mode 工作台 API ====================

/**
 * 获取 Agent Mode 直播托管工作台数据
 */
export async function getAgentModeWorkbench() {
    return request('/api/agent-mode/workbench');
}

/**
 * 更新 Agent Mode 直播托管工作台数据
 */
export async function updateAgentModeWorkbench(data) {
    return request('/api/agent-mode/workbench', {
        method: 'PUT',
        body: JSON.stringify(data),
    });
}

// ==================== 竞价 API ====================

/**
 * 计算竞价
 */
export async function calculateBid(campaignId, pValue, userFeatures = {}) {
    return request('/api/bidding/calculate', {
        method: 'POST',
        body: JSON.stringify({
            campaign_id: campaignId,
            p_value: pValue,
            user_features: userFeatures,
        }),
    });
}

/**
 * 模拟竞价过程
 */
export async function simulateBidding(campaignId, steps = 48) {
    return request(`/api/bidding/simulate?campaign_id=${campaignId}&steps=${steps}`, {
        method: 'POST',
    });
}

// ==================== AI 诊断 API ====================

/**
 * 获取智能诊断
 */
export async function getDiagnosis() {
    return request('/api/diagnosis');
}

/**
 * AI 对话
 */
export async function chatWithAI(message) {
    return request(`/api/ai/chat?message=${encodeURIComponent(message)}`, {
        method: 'POST',
    });
}

/**
 * 获取 Agent 可用模型
 */
export async function getAgentModels() {
    return request('/api/ai/models');
}

/**
 * 获取 Agent 可访问的数据源
 */
export async function getAgentDataSources() {
    return request('/api/ai/data-sources');
}

/**
 * Agent 对话 (流式响应)
 * @param {Array} messages - 对话历史 [{role: 'user', content: '...'}, ...]
 * @param {Function} onMessage - 收到消息时的回调 (data) => void
 * @param {Function} onToolCall - 工具调用时的回调 (tool, args) => void
 * @param {Function} onToolResult - 工具结果时的回调 (tool, result) => void
 * @param {Function} onError - 错误时的回调 (error) => void
 * @param {Function} onDone - 完成时的回调 () => void
 */
export async function chatWithAgent(
    messages,
    { onMessage, onToolCall, onToolResult, onError, onDone, onModel } = {},
    options = {}
) {
    const url = `${API_BASE_URL}/api/ai/agent`;

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                messages,
                enable_tools: true,
                model: options.model,
                models: options.models,
                enabled_data_sources: options.enabledDataSources,
            }),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        switch (data.type) {
                            case 'content':
                                onMessage?.(data.content);
                                break;
                            case 'tool_call':
                                onToolCall?.(data.tool, data.arguments);
                                break;
                            case 'tool_result':
                                onToolResult?.(data.tool, data.result);
                                break;
                            case 'model':
                                onModel?.(data.model);
                                break;
                            case 'error':
                                onError?.(data.content);
                                break;
                            case 'done':
                                onDone?.();
                                break;
                        }
                    } catch (e) {
                        // 忽略解析错误
                    }
                }
            }
        }
    } catch (error) {
        console.error('Agent chat failed:', error);
        onError?.(error.message);
    }
}

// ==================== Orchestrator API ====================

export async function chatWithOrchestrator(
    messages,
    { onMessage, onToolCall, onToolResult, onError, onDone, onModel,
      onWorkbenchPatch, onViewSwitch, onPhaseChange, onAgentAction } = {},
) {
    const url = `${API_BASE_URL}/api/orchestrator/chat`;

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages, enable_tools: true }),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        switch (data.type) {
                            case 'content':
                                onMessage?.(data.content);
                                break;
                            case 'tool_call':
                                onToolCall?.(data.tool, data.arguments);
                                break;
                            case 'tool_result':
                                onToolResult?.(data.tool, data.result);
                                break;
                            case 'workbench_patch':
                                onWorkbenchPatch?.(data.patch);
                                break;
                            case 'view_switch':
                                onViewSwitch?.(data.view);
                                break;
                            case 'phase_change':
                                onPhaseChange?.(data.phase);
                                break;
                            case 'agent_action':
                                onAgentAction?.(data.event);
                                break;
                            case 'model':
                                onModel?.(data.model);
                                break;
                            case 'error':
                                onError?.(data.content);
                                break;
                            case 'done':
                                onDone?.();
                                break;
                        }
                    } catch (e) {
                        // ignore parse errors
                    }
                }
            }
        }
    } catch (error) {
        console.error('Orchestrator chat failed:', error);
        onError?.(error.message);
    }
}

export async function resetWorkbench() {
    return request('/api/workbench/reset', { method: 'POST' });
}

export async function getWorkbenchState() {
    return request('/api/workbench/state');
}

// ==================== 健康检查 ====================

/**
 * 检查 API 服务状态
 */
export async function healthCheck() {
    return request('/health');
}

export default {
    getCampaigns,
    getCampaign,
    createCampaign,
    updateCampaign,
    deleteCampaign,
    toggleCampaignStatus,
    getRealtimeMetrics,
    getMetricsTrend,
    getAgentModeWorkbench,
    updateAgentModeWorkbench,
    calculateBid,
    simulateBidding,
    getDiagnosis,
    chatWithAI,
    getAgentModels,
    getAgentDataSources,
    chatWithAgent,
    chatWithOrchestrator,
    resetWorkbench,
    getWorkbenchState,
    healthCheck,
};
