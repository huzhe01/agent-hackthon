from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AgentBackendFrontendTest(unittest.TestCase):
    def test_agent_backend_route_is_registered(self):
        app_source = (ROOT / "frontend/src/App.jsx").read_text(encoding="utf-8")

        self.assertIn("AgentBackendPage", app_source)
        self.assertIn("'/agentbackend'", app_source)
        self.assertLess(
            app_source.index("'/agentbackend'"),
            app_source.index("return <ManualWorkbenchPage />"),
        )

    def test_agent_backend_page_shows_model_and_data_linkage(self):
        page_path = ROOT / "frontend/src/agent-backend/AgentBackendPage.jsx"
        self.assertTrue(page_path.exists())

        page_source = page_path.read_text(encoding="utf-8")
        for marker in [
            "MaiDeal 后端模型中台",
            "数据收集",
            "预估模型",
            "预算控制模型",
            "流量预估模型",
            "Agent 迭代",
            "ad_rec_backend",
            "Supabase 持久化",
            "Qiji Agent Runtime",
            "FlowPacket",
            "setActiveNode",
            "/api/agent-runtime/run",
        ]:
            self.assertIn(marker, page_source)


if __name__ == "__main__":
    unittest.main()
