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
            app_source.index("return <ManualWorkbenchPage />"),
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
            "MaiDeal工作台",
            "投放方案",
            "在线看板",
            "盘后迭代",
            "数据资产",
            "便携榨汁杯",
            "托管顾问",
            "选择并启动",
        ]:
            self.assertIn(required_text, searchable_source)

        self.assertNotIn("MaiDeal 直播后台", page_source)
        self.assertNotIn("MaiDeal工作台 ·", page_source)
        self.assertNotIn("直播后台</div>", page_source)
        self.assertNotIn("广告主预算全托管 · 直播间投流工作台", page_source)
        for retired_stage_label in ["方案规划", "直播托管", "复盘迭代"]:
            self.assertNotIn(f"label: '{retired_stage_label}'", page_source)

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

    def test_agent_mode_left_sidebar_manages_budget_projects_with_compact_agent_status(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")
        left_panel_source = page_source[
            page_source.index("function LeftPanel"):
            page_source.index("function MetricPill")
        ]

        for required_marker in [
            "预算项目历史",
            "BudgetProjectHistoryList",
            "AgentStatusDock",
            "子 Agent 状态",
            "onSelectBudgetProject",
            "budgetProjects.map",
            "agentRoster.map",
        ]:
            self.assertIn(required_marker, left_panel_source)

        for removed_marker in [
            "项目 brief",
            "BriefFieldGrid",
            "leftTimeline.map",
            "托管模块状态",
            "已收集：",
            "project.budget",
            "project.spent",
            "project.roas",
            "当前预算项目",
            "projectBrief",
            "activeProject",
            "onReset",
        ]:
            self.assertNotIn(removed_marker, left_panel_source)

    def test_agent_mode_plan_canvas_uses_channel_list_for_live_room_switching(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")
        plan_canvas_source = page_source[
            page_source.index("function PlanCanvas"):
            page_source.index("function LiveLoopPanel")
        ]

        for marker in [
            "ChannelPlanSelector",
            "渠道 / 直播间",
            "activeRoom",
            "md:grid-cols-[240px_minmax(0,1fr)]",
            "模式方案",
            "liveRooms.map",
            "planOptions.map",
        ]:
            self.assertIn(marker, plan_canvas_source)

        self.assertNotIn("<LiveRoomCard", plan_canvas_source)
        self.assertNotIn("grid grid-cols-3 gap-4", plan_canvas_source)
        self.assertNotIn("项目摘要", plan_canvas_source)

    def test_agent_mode_plan_versions_are_kept_in_data_but_hidden_from_canvas(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")
        defaults_source = (ROOT / "frontend/src/agent-mode/agentModeDefaults.js").read_text(encoding="utf-8")
        backend_source = (ROOT / "backend/orchestrator.py").read_text(encoding="utf-8")

        self.assertIn("plan_versions", defaults_source + backend_source)
        self.assertNotIn("PlanVersionList", page_source)
        self.assertNotIn("方案版本", page_source)
        self.assertNotIn("currentPlanVersions", page_source)

        self.assertIn("plan.recommended", page_source)
        self.assertIn("room.recommended", page_source)
        self.assertNotIn("selected && <span", page_source)
        self.assertNotIn("plan.id === 'balanced' && <span", page_source)

    def test_agent_mode_budget_history_fills_left_panel_space(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")
        left_panel_source = page_source[
            page_source.index("function LeftPanel"):
            page_source.index("function MetricPill")
        ]

        self.assertIn("min-h-0 flex flex-1 flex-col overflow-y-auto p-3", left_panel_source)
        self.assertIn('GlassCard className="mt-3 flex-1 p-3"', left_panel_source)

    def test_agent_mode_budget_project_history_rows_are_title_only(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")
        history_source = page_source[
            page_source.index("function BudgetProjectHistoryList"):
            page_source.index("function AgentStatusDock")
        ]

        self.assertIn("project.name", history_source)
        self.assertIn("onSelectBudgetProject", history_source)

        for hidden_detail in [
            "project.status",
            "project.budget",
            "project.spent",
            "project.roas",
            "当前",
            "待托管",
        ]:
            self.assertNotIn(hidden_detail, history_source)

    def test_agent_mode_can_add_blank_budget_project_without_demo_data(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")

        for marker in [
            "onCreateBudgetProject",
            "新增项目",
            "createBlankBudgetProject",
            "blank-agent-project",
            "lead_rows: []",
            "fallback_campaigns: []",
            "review_actions: []",
            "strategy_notes: []",
            "sku_ads: []",
            "metrics: { spend: 0, revenue: 0, profit: 0, roas: 0, cpa: 0, inventory: 0 }",
            "parseMoneyValue(goal.totalBudgetValue || goal.totalBudget, 0)",
        ]:
            self.assertIn(marker, page_source)

        for list_source_marker in [
            "Array.isArray(wb.lead_rows)",
            "Array.isArray(wb.review_actions)",
            "Array.isArray(wb.strategy_notes)",
            "Array.isArray(wb.fallback_campaigns)",
        ]:
            self.assertIn(list_source_marker, page_source)

    def test_agent_mode_live_budget_pool_appears_before_strategy_loop(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")
        live_canvas_source = page_source[
            page_source.index("function LiveCanvas"):
            page_source.index("function LeadsCanvas")
        ]

        self.assertLess(
            live_canvas_source.index("统一预算池"),
            live_canvas_source.index("<LiveLoopPanel"),
        )

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
            "tick_interval_ms: 5000",
            "currentActiveAlert",
            "approvalPauseRef",
        ]:
            self.assertIn(ui_marker, page_source + defaults_source)

        for removed_demo_button in [
            "运行一轮投中巡检",
            "模拟高风险动作",
            "人工接管",
            "人工接管中",
            "已暂停巡检",
            "持续自动巡检",
        ]:
            self.assertNotIn(removed_demo_button, page_source)

        self.assertIn("api.chatWithOrchestrator", page_source)
        self.assertIn("setLiveDemoPlaying(false)", page_source)
        self.assertIn("setLiveDemoPlaying(true)", page_source)

    def test_agent_mode_live_demo_final_frame_is_persisted_for_history(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")

        for marker in [
            "getProjectLiveDemoFinalIndex",
            "shouldOpenProjectAtFinalFrame",
            "finalizeActiveBudgetProjectSnapshot",
            "setLiveDemoIndex(getProjectLiveDemoFinalIndex(selectedProject))",
            "const responseProject = { ...selectedProject, workbench: response }",
            "setLiveDemoIndex(getProjectLiveDemoFinalIndex(responseProject))",
            "response.phase === 'review' || response.review_ready",
            "liveDemoCompleted",
        ]:
            self.assertIn(marker, page_source)

    def test_agent_mode_budget_alert_approval_updates_workbench_budget_pool(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")

        for marker in [
            "applyBudgetApprovalToLiveDemo",
            "buildBudgetApprovalPatch",
            "isBudgetApprovalAction",
            "approved_budget_amount",
            "api.updateAgentModeWorkbench(nextPatch)",
            "预算审批已写入",
        ]:
            self.assertIn(marker, page_source)

    def test_agent_mode_agent_roster_status_tracks_plan_live_and_review(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")

        for marker in [
            "deriveAgentRosterStatuses",
            "derivedAgentRoster",
            "phase === 'planning'",
            "方案已生成",
            "投放执行",
            "liveDemoCompleted ? '完成' : '执行中'",
            "reviewReady || phase === 'review'",
            "效果分析",
            "经营信号",
            "status: '完成'",
            "agentRoster={derivedAgentRoster}",
        ]:
            self.assertIn(marker, page_source)

    def test_agent_mode_prompt_plan_launch_and_review_are_gated(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")

        for marker in [
            "已经检索历史的信息和新闻",
            "选择并启动",
            "onStartManagedDelivery(plan.id, plan.title)",
            "runOrchestratorCommand(`选择${planTitle}方案`, { echoUser: false })",
            "setLiveDemoIndex(0)",
            "patch.live_demo",
            "setLiveDemoPlaying(false)",
            "newPhase === 'live') {\n            setActiveStage('live');\n            setLiveDemoIndex(0);\n            setLiveDemoPlaying(true);",
            "Math.min(index + 1, liveDemoFrames.length - 1)",
            "const liveDemoCompleted",
            "reviewReady",
            "在线看板跑完后，盘后迭代会自动生成",
            "pending_review",
            "goal?.targetRoas || '3.0'",
            "goal={goal}",
        ]:
            self.assertIn(marker, page_source)

        for removed_marker in [
            "(index + 1) % liveDemoFrames.length",
            "批准并启动托管",
        ]:
            self.assertNotIn(removed_marker, page_source)

    def test_agent_mode_plan_generation_uses_five_second_loading_gate(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")

        for marker in [
            "const PLAN_REVEAL_DELAY_MS = 5000",
            "function PlanGeneratingCanvas",
            "planRevealPending",
            "startPlanRevealDelay",
            "shouldDelayPlanReveal",
            "window.setTimeout(() => setPlanRevealPending(false), PLAN_REVEAL_DELAY_MS)",
            "正在生成投放方案",
            "planRevealPending={planRevealPending}",
        ]:
            self.assertIn(marker, page_source)

    def test_agent_mode_terminal_live_state_releases_review_canvas(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")
        live_render_source = page_source[
            page_source.index("props.activeStage === 'live'"):
            page_source.index("props.activeStage === 'review'")
        ]
        canvas_props_source = page_source[
            page_source.index("const canvasProps = {"):
            page_source.index("const themeClass")
        ]

        for marker in [
            "isTerminalLiveFrame",
            "reviewReleaseReady",
            "terminalLiveFrame",
            "reviewReady={reviewReady}",
            "验证已完成，盘后迭代已生成",
        ]:
            self.assertIn(marker, page_source)

        self.assertIn("reviewReady={props.reviewReady}", live_render_source)
        self.assertIn("reviewReady,", canvas_props_source)

    def test_agent_mode_review_owns_lead_assets_and_report_generation(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")

        for required_marker in [
            "数据资产",
            "线索资产",
            "/api/agent-mode/workbench",
            "/api/metrics/realtime",
            "/api/metrics/trend?hours=24",
            "/api/campaigns",
            "/api/orchestrator/chat",
            "reviewReportStreaming",
            "generateReviewReport",
            "api.chatWithOrchestrator",
            "onMessage: (chunk)",
        ]:
            self.assertIn(required_marker, page_source)

        self.assertNotIn("function ReviewReportCard", page_source)
        self.assertNotIn("{ id: 'leads'", page_source)
        self.assertNotIn("props.activeStage === 'leads'", page_source)

    def test_agent_mode_review_generation_is_delayed_and_has_journey_chart(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")

        for marker in [
            "const REVIEW_REVEAL_DELAY_MS = 5000",
            "function ReviewGeneratingCanvas",
            "reviewRevealPending",
            "startReviewRevealDelay",
            "ReviewJourneyChart",
            "AI 正在生成盘后迭代",
            "投放全过程曲线",
            "liveDemoFrames={props.liveDemoFrames}",
            "liveDemoFrames={liveDemoFrames}",
            "window.setTimeout(() => setReviewRevealPending(false), REVIEW_REVEAL_DELAY_MS)",
        ]:
            self.assertIn(marker, page_source)

        review_render_source = page_source[
            page_source.index("return (\n    <div className=\"mx-auto flex max-w-6xl flex-col gap-5\">", page_source.index("function ReviewCanvas")):
            page_source.index("{(reviewReportStreaming || reviewReportText || reviewReportError) && (")
        ]
        data_asset_index = review_render_source.index("线索资产已并入复盘")
        chart_index = review_render_source.index("<ReviewJourneyChart frames={liveDemoFrames} />")
        action_index = review_render_source.index("关键动作回顾")
        self.assertLess(data_asset_index, chart_index)
        self.assertLess(chart_index, action_index)

    def test_agent_mode_canvas_header_removed_and_focus_lives_in_stage_panels(self):
        page_source = (ROOT / "frontend/src/agent-mode/AgentModePage.jsx").read_text(encoding="utf-8")

        self.assertNotIn("function CanvasHeader", page_source)
        self.assertNotIn("工作画布</span>", page_source)
        self.assertNotIn("<CanvasHeader", page_source)
        self.assertIn("FocusModeButton", page_source)
        self.assertIn("专注模式", page_source)

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
            "Planning Agent 输出",
            "Delivery Agent 运行中",
            "Signal Agent 实时建档",
            "Analysis Agent 输出",
        ]:
            self.assertNotIn(ai_heavy_label, page_source)


if __name__ == "__main__":
    unittest.main()
