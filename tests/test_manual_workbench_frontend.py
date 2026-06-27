from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ManualWorkbenchFrontendTest(unittest.TestCase):
    def test_root_route_renders_manual_workbench_and_keeps_agent_mode_separate(self):
        app_source = (ROOT / "frontend/src/App.jsx").read_text(encoding="utf-8")

        self.assertIn("ManualWorkbenchPage", app_source)
        self.assertIn("AgentModePage", app_source)
        self.assertIn("'/agent-mode'", app_source)
        self.assertIn("return <ManualWorkbenchPage />", app_source)
        self.assertLess(
            app_source.index("'/agent-mode'"),
            app_source.index("return <ManualWorkbenchPage />"),
        )
        self.assertNotIn("return <DashboardApp />", app_source)

    def test_manual_workbench_reuses_agent_mode_business_context(self):
        page_path = ROOT / "frontend/src/manual-workbench/ManualWorkbenchPage.jsx"
        self.assertTrue(page_path.exists())
        page_source = page_path.read_text(encoding="utf-8")

        for required_marker in [
            "agentModeFallback",
            "budget_projects",
            "live_demo",
            "人工操作台",
            "预算项目历史",
            "手动预算分配",
            "直播托管控制台",
            "商品 SKU 投放",
            "人工审批队列",
            "操作记录",
            "切换 Agent Mode",
        ]:
            self.assertIn(required_marker, page_source)

    def test_manual_workbench_removes_legacy_generic_ads_navigation(self):
        page_source = (ROOT / "frontend/src/manual-workbench/ManualWorkbenchPage.jsx").read_text(encoding="utf-8")

        for legacy_marker in [
            "GrowEngine",
            "财务管理",
            "投放工具",
            "系统设置",
            "文档站",
            "智能诊断",
            "Agent 对话",
            "托管顾问",
            "chatWithOrchestrator",
        ]:
            self.assertNotIn(legacy_marker, page_source)
