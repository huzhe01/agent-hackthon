from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AgentModeFrontendTest(unittest.TestCase):
    def test_agent_mode_route_is_registered(self):
        app_source = (ROOT / "frontend/src/App.jsx").read_text(encoding="utf-8")

        self.assertIn("AgentModePage", app_source)
        self.assertIn("'/agent-mode'", app_source)
        self.assertLess(
            app_source.index("'/agent-mode'"),
            app_source.index("return <DashboardApp />"),
        )

    def test_agent_mode_page_contains_core_workbench_sections(self):
        page_path = ROOT / "frontend/src/agent-mode/AgentModePage.jsx"
        self.assertTrue(page_path.exists())

        page_source = page_path.read_text(encoding="utf-8")
        defaults_path = ROOT / "frontend/src/agent-mode/agentModeDefaults.js"
        searchable_source = page_source
        if defaults_path.exists():
            searchable_source += defaults_path.read_text(encoding="utf-8")

        for required_text in [
            "MaiDeal 直播后台",
            "方案规划",
            "直播托管",
            "复盘迭代",
            "数据资产",
            "便携榨汁杯",
            "托管顾问",
            "批准并启动托管",
        ]:
            self.assertIn(required_text, searchable_source)

    def test_agent_mode_page_uses_existing_agent_and_metrics_apis(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")

        for api_call in [
            "api.getAgentModeWorkbench",
            "api.getRealtimeMetrics",
            "api.getMetricsTrend",
            "api.getCampaigns",
            "api.getAgentModels",
            "api.getAgentDataSources",
            "api.chatWithOrchestrator",
            "api.resetWorkbench",
        ]:
            self.assertIn(api_call, page_source)

        for state_name in ["leftCollapsed", "rightCollapsed", "focusMode"]:
            self.assertIn(state_name, page_source)

    def test_agent_mode_business_seed_data_is_not_hardcoded_in_page(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")
        defaults_source = ROOT / "frontend/src/agent-mode/agentModeDefaults.js"
        api_source = (ROOT / "frontend/src/services/api.js").read_text(encoding="utf-8")

        self.assertTrue(defaults_source.exists())
        self.assertIn("agentModeFallback", page_source)
        self.assertIn("getAgentModeWorkbench", api_source)
        self.assertIn("updateAgentModeWorkbench", api_source)
        self.assertIn("/api/agent-mode/workbench", api_source)

        for removed_page_constant in [
            "const liveRooms",
            "const leftTimeline",
            "const agentRoster",
            "const leadRows",
            "const fallbackCampaigns",
            "东南亚手机壳直播",
            "磁吸手机壳 Pro",
            "@jenny_w",
            "库存 1200 件，毛利率 55%",
        ]:
            self.assertNotIn(removed_page_constant, page_source)

        defaults_text = defaults_source.read_text(encoding="utf-8")
        self.assertIn("东南亚手机壳直播", defaults_text)
        self.assertIn("磁吸手机壳 Pro", defaults_text)

    def test_agent_mode_budget_project_history_can_select_mock_projects(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")
        defaults_source = (ROOT / "frontend/src/agent-mode/agentModeDefaults.js").read_text(encoding="utf-8")

        for ui_marker in [
            "budget_projects",
            "activeBudgetProjectId",
            "onSelectBudgetProject",
            "预算项目历史",
            "历史预算项目",
            "phonecase-sea-live",
        ]:
            self.assertIn(ui_marker, page_source + defaults_source)

        self.assertIn("东南亚手机壳直播", defaults_source)
        self.assertIn("手机壳直播间 A · 达人测评", defaults_source)
        self.assertIn("磁吸手机壳 Pro", defaults_source)

    def test_agent_mode_left_sidebar_only_manages_budget_projects(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")
        left_panel_source = page_source[
            page_source.index("function LeftPanel"):
            page_source.index("function MetricPill")
        ]

        for required_marker in [
            "当前预算项目",
            "预算项目历史",
            "onSelectBudgetProject",
            "budgetProjects.map",
        ]:
            self.assertIn(required_marker, left_panel_source)

        for removed_marker in [
            "项目 brief",
            "BriefFieldGrid",
            "leftTimeline.map",
            "托管模块状态",
            "agentRoster.map",
            "已收集：",
        ]:
            self.assertNotIn(removed_marker, left_panel_source)

    def test_agent_mode_plan_versions_are_rendered_in_canvas(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")
        defaults_source = (ROOT / "frontend/src/agent-mode/agentModeDefaults.js").read_text(encoding="utf-8")
        backend_source = (ROOT / "backend/orchestrator.py").read_text(encoding="utf-8")

        for marker in [
            "plan_versions",
            "PlanVersionList",
            "方案版本",
            "currentPlanVersions",
        ]:
            self.assertIn(marker, page_source + defaults_source + backend_source)

        self.assertIn("plan.recommended", page_source)
        self.assertIn("room.recommended", page_source)
        self.assertNotIn("selected && <span", page_source)
        self.assertNotIn("plan.id === 'balanced' && <span", page_source)

    def test_agent_mode_has_drag_resize_controls(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")

        for ui_marker in [
            "leftPanelWidth",
            "rightPanelWidth",
            "createResizePointerDown",
            "拖动调整左侧栏宽度",
            "拖动调整右侧栏宽度",
            "cursor-col-resize",
        ]:
            self.assertIn(ui_marker, page_source)

        for removed_marker in [
            "function WidthMenu",
            "rightWidthOpen",
            "setRightWidthOpen",
            "自定义宽度",
            "紧凑",
            "标准",
            "宽屏",
            "向 Orchestrator 提问 / 下达指令",
        ]:
            self.assertNotIn(removed_marker, page_source)

    def test_agent_mode_live_demo_uses_sequence_without_manual_scan_buttons(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")
        defaults_source = (ROOT / "frontend/src/agent-mode/agentModeDefaults.js").read_text(encoding="utf-8")

        for ui_marker in [
            "持续策略与执行闭环",
            "直播中",
            "商品 SKU 投放",
            "自动预警",
            "live_demo",
            "liveDemoPlaying",
            "currentLiveFrame",
            "budget_pool",
            "sku_ads",
            "tick_interval_ms: 60000",
            "onPauseLiveDemo",
            "onTakeOverLiveDemo",
            "已暂停巡检",
        ]:
            self.assertIn(ui_marker, page_source + defaults_source)

        for removed_demo_button in [
            "运行一轮投中巡检",
            "模拟高风险动作",
        ]:
            self.assertNotIn(removed_demo_button, page_source)

        self.assertIn("api.chatWithOrchestrator", page_source)

    def test_agent_mode_review_owns_lead_assets_and_report_generation(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")

        for required_marker in [
            "数据资产",
            "线索资产",
            "本场复盘报告",
            "API 调用链",
            "/api/agent-mode/workbench",
            "/api/metrics/realtime",
            "/api/metrics/trend?hours=24",
            "/api/campaigns",
            "/api/orchestrator/chat",
            "showReviewReport",
        ]:
            self.assertIn(required_marker, page_source)

        self.assertNotIn("{ id: 'leads'", page_source)
        self.assertNotIn("props.activeStage === 'leads'", page_source)

    def test_agent_mode_defaults_to_light_theme_with_manual_theme_switch(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")
        css_source = (ROOT / "frontend/src/index.css").read_text(encoding="utf-8")

        for ui_marker in [
            "useState('light')",
            "agent-mode-light",
            "agent-mode-dark",
            "切换为浅色主题",
            "切换为深色主题",
            "浅色",
            "深色",
            "直播后台",
            "托管顾问",
        ]:
            self.assertIn(ui_marker, page_source)

        for css_marker in [
            ".agent-mode-light",
            ".agent-mode-light .bg-\\[\\#070b13\\]",
            ".agent-mode-light .text-white",
            ".agent-mode-light textarea",
        ]:
            self.assertIn(css_marker, css_source)

        for ai_heavy_label in [
            "Agent Mode</span>",
            "Agent 对话</span>",
            "子 Agent 状态</div>",
            "Planning Agent 输出",
            "Delivery Agent 运行中",
            "Signal Agent 实时建档",
            "Analysis Agent 输出",
        ]:
            self.assertNotIn(ai_heavy_label, page_source)


if __name__ == "__main__":
    unittest.main()
