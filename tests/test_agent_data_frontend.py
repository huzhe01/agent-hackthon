from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AgentDataFrontendTest(unittest.TestCase):
    def test_agent_data_route_is_registered(self):
        app_source = (ROOT / "frontend/src/App.jsx").read_text(encoding="utf-8")

        self.assertIn("AgentDataPage", app_source)
        self.assertIn("'/agent-data'", app_source)
        self.assertLess(
            app_source.index("'/agent-data'"),
            app_source.index("return <ManualWorkbenchPage />"),
        )

    def test_agent_data_page_shows_dynamic_data_and_model_flow(self):
        page_path = ROOT / "frontend/src/agent-data/AgentDataPage.jsx"
        self.assertTrue(page_path.exists())

        page_source = page_path.read_text(encoding="utf-8")
        for marker in [
            "MaiDeal 数据系统",
            "数据流入",
            "模型预估",
            "Agent 编排",
            "媒体 API",
            "客户授权 API",
            "模拟器兜底",
            "预算分配模型",
            "GMV = Σ SKU 成交额",
            "ROAS = GMV / Spend",
            "FlowPacket",
            "setActiveStep",
        ]:
            self.assertIn(marker, page_source)


if __name__ == "__main__":
    unittest.main()
