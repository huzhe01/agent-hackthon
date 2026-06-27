import importlib
import os
import unittest


class AgentLoopConfigTest(unittest.TestCase):
    def setUp(self):
        self.original_env = os.environ.copy()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_qiji_config_defaults_to_verified_model(self):
        os.environ.pop("QIJI_BASE_URL", None)
        os.environ.pop("QIJI_MODEL", None)
        os.environ.pop("QIJI_API_KEY", None)
        os.environ.pop("LLM_API_KEY", None)

        api = importlib.import_module("backend.api")
        importlib.reload(api)

        config = api.get_qiji_config()

        self.assertEqual(config["api_base"], "https://api.openai-next.com/v1")
        self.assertEqual(config["model"], "gpt-5")
        self.assertEqual(config["api_key"], "")

    def test_agent_data_sources_default_to_all_enabled(self):
        api = importlib.import_module("backend.api")
        importlib.reload(api)

        sources = api.get_agent_data_sources()

        self.assertGreaterEqual(len(sources), 7)
        self.assertTrue(all(source["enabled_by_default"] for source in sources))
        self.assertEqual(
            [source["id"] for source in sources],
            [
                "realtime_metrics",
                "trend_metrics",
                "campaigns",
                "diagnosis",
                "product_ads",
                "creative_library",
                "business_clues",
            ],
        )

    def test_agent_tools_are_filtered_by_selected_data_sources(self):
        api = importlib.import_module("backend.api")
        importlib.reload(api)

        tools = api.build_agent_tools(["campaigns", "creative_library"])
        tool_names = [tool["function"]["name"] for tool in tools]

        self.assertIn("get_campaigns", tool_names)
        self.assertIn("get_creative_library", tool_names)
        self.assertIn("create_campaign_preview", tool_names)
        self.assertNotIn("get_realtime_metrics", tool_names)
        self.assertNotIn("get_diagnosis", tool_names)
        self.assertNotIn("search_business_clues", tool_names)

    def test_business_clues_tool_is_enabled_by_data_source(self):
        api = importlib.import_module("backend.api")
        importlib.reload(api)

        tools = api.build_agent_tools(["business_clues"])
        tool_names = [tool["function"]["name"] for tool in tools]

        self.assertIn("search_business_clues", tool_names)
        self.assertIn("create_campaign_preview", tool_names)
        self.assertNotIn("get_campaigns", tool_names)

    def test_model_options_keep_verified_gpt5_as_default(self):
        api = importlib.import_module("backend.api")
        importlib.reload(api)

        models = api.get_agent_model_options(["dall-e-3", "gpt-4o", "gpt-5", "flux"])

        self.assertEqual(models[0]["id"], "gpt-5")
        self.assertTrue(models[0]["enabled_by_default"])
        self.assertEqual([model["id"] for model in models], ["gpt-5", "gpt-4o"])

    def test_model_options_prioritize_verified_qiji_chat_models(self):
        api = importlib.import_module("backend.api")
        importlib.reload(api)

        models = api.get_agent_model_options([
            "deepseek-chat",
            "gpt-5-nano",
            "gpt-5.5",
            "gpt-5",
            "qwen-max",
            "gpt-4o-image",
            "gpt-5-mini",
        ])

        self.assertEqual(
            [model["id"] for model in models[:5]],
            ["gpt-5", "gpt-5.5", "gpt-5-mini", "gpt-5-nano", "qwen-max"],
        )
        self.assertIn("deepseek-chat", [model["id"] for model in models])
        self.assertNotIn("gpt-4o-image", [model["id"] for model in models])

    def test_xiaosu_search_config_supports_cloudsway_key(self):
        os.environ["CLOUDSWAY_SEARCH_KEY"] = "cloudsway-test-key"
        os.environ["XIAOSU_SEARCH_API_KEY"] = "legacy-test-key"

        api = importlib.import_module("backend.api")
        importlib.reload(api)

        config = api.get_xiaosu_search_config()

        self.assertEqual(config["api_base"], "https://aisearchapi.cloudsway.net/api/search/smart")
        self.assertEqual(config["api_key"], "cloudsway-test-key")

    def test_search_business_clues_without_key_returns_setup_hint(self):
        os.environ.pop("CLOUDSWAY_SEARCH_KEY", None)
        os.environ.pop("XIAOSU_SEARCH_API_KEY", None)

        api = importlib.import_module("backend.api")
        importlib.reload(api)

        result = api.execute_tool("search_business_clues", {"query": "TikTok Shop 美妆直播 趋势"})

        self.assertFalse(result["success"])
        self.assertEqual(result["type"], "business_clues")
        self.assertIn("CLOUDSWAY_SEARCH_KEY", result["error"])

    def test_agent_mode_workbench_can_be_read_and_updated(self):
        api = importlib.import_module("backend.api")
        importlib.reload(api)
        api.reset_workbench()

        workbench = api.get_agent_mode_workbench()

        self.assertIn("project", workbench)
        self.assertIn("live_rooms", workbench)
        self.assertIn("left_timeline", workbench)
        self.assertIn("agent_roster", workbench)
        self.assertIn("live_loop", workbench)
        self.assertIn("live_demo", workbench)
        self.assertIn("budget_projects", workbench)
        self.assertIn("active_project_id", workbench)
        self.assertEqual(workbench["project"]["product"], "")
        self.assertEqual(workbench["live_loop"]["status"], "idle")

        budget_projects = workbench["budget_projects"]
        self.assertGreaterEqual(len(budget_projects), 2)
        self.assertTrue(any(project["id"] == "blender-us-live" for project in budget_projects))
        sea_project = next(project for project in budget_projects if project["id"] == "phonecase-sea-live")
        self.assertEqual(sea_project["name"], "东南亚手机壳直播")
        self.assertEqual(sea_project["budget"], "$3,200")
        self.assertIn("workbench", sea_project)
        self.assertEqual(sea_project["workbench"]["project"]["product"], "磁吸手机壳")
        self.assertEqual(sea_project["workbench"]["project"]["market"], "东南亚 / SGD")
        self.assertTrue(sea_project["workbench"]["live_demo"]["frames"])
        self.assertEqual(sea_project["workbench"]["live_demo"]["frames"][0]["sku_ads"][0]["name"], "磁吸手机壳 Pro")

        frames = workbench["live_demo"]["frames"]
        self.assertEqual(workbench["live_demo"]["tick_interval_ms"], 10000)
        self.assertGreaterEqual(len(frames), 6)
        for frame_key in ["metrics", "budget_pool", "sku_ads", "events", "steps"]:
            self.assertIn(frame_key, frames[0])
        self.assertTrue(any(frame.get("alerts") for frame in frames))
        self.assertTrue(any(alert["type"] in {"roi_low", "budget_low"} for frame in frames for alert in frame.get("alerts", [])))

        updated = api.update_agent_mode_workbench({
            "project": {"product": "测试商品"},
            "layout": {"left_panel_width": 330, "right_panel_width": 460},
        })

        self.assertEqual(updated["project"]["product"], "测试商品")
        self.assertEqual(updated["layout"]["left_panel_width"], 330)
        self.assertEqual(updated["layout"]["right_panel_width"], 460)


if __name__ == "__main__":
    unittest.main()
