import json
import tempfile
import unittest
from pathlib import Path


class AgentToolRegistryTest(unittest.TestCase):
    def test_registry_exposes_requested_tool_schemas(self):
        from backend.agent.registry import get_agent_tool_schemas, list_agent_tools

        expected = {
            "estimate_ad_performance",
            "query_backend_database",
            "generate_marketing_content",
            "allocate_budget",
            "inspect_media_api",
            "refresh_business_knowledge",
            "simulate_live_workbench",
        }

        tools = list_agent_tools()
        self.assertTrue(expected.issubset({tool["name"] for tool in tools}))

        schemas = get_agent_tool_schemas()
        schema_names = {schema["function"]["name"] for schema in schemas}
        self.assertTrue(expected.issubset(schema_names))
        for schema in schemas:
            self.assertEqual(schema["type"], "function")
            self.assertIn("description", schema["function"])
            self.assertIn("parameters", schema["function"])

    def test_budget_allocator_respects_budget_and_roi_order(self):
        from backend.agent.registry import dispatch_agent_tool

        result = dispatch_agent_tool(
            "allocate_budget",
            {
                "total_budget": 1000,
                "channels": [
                    {"id": "tiktok", "label": "TikTok Ads", "roi": 2.0, "min_budget": 100, "max_budget": 500},
                    {"id": "meta", "label": "Meta Ads", "roi": 3.2, "min_budget": 100, "max_budget": 700},
                    {"id": "shopee", "label": "Shopee Ads", "roi": 2.6, "min_budget": 100, "max_budget": 400},
                ],
            },
        )

        self.assertTrue(result["success"])
        allocations = {row["id"]: row["allocated_budget"] for row in result["allocations"]}
        self.assertEqual(sum(allocations.values()), 1000)
        self.assertGreaterEqual(allocations["meta"], allocations["shopee"])
        self.assertGreaterEqual(allocations["shopee"], allocations["tiktok"])
        self.assertIn("linear", result["method"])

    def test_simulator_tool_returns_dynamic_bundle_with_five_skus(self):
        from backend.agent.registry import dispatch_agent_tool

        result = dispatch_agent_tool(
            "simulate_live_workbench",
            {
                "brief": {
                    "budget": 5000,
                    "target_roas": 3.0,
                    "products": "便携榨汁杯",
                    "market": "美国 / USD",
                    "channels": "TikTok + Meta",
                    "inventory": 1200,
                },
                "version_number": 2,
            },
        )

        self.assertTrue(result["success"])
        self.assertEqual(len(result["product_catalog"]), 5)
        self.assertEqual(len(result["channel_pools"]), 2)
        self.assertGreaterEqual(result["frames_count"], 6)
        final_metrics = result["final_frame"]["metrics"]
        self.assertAlmostEqual(final_metrics["revenue"] / final_metrics["spend"], final_metrics["roas"], delta=0.15)

    def test_knowledge_tool_persists_search_results_and_memory(self):
        from backend.agent.registry import dispatch_agent_tool

        with tempfile.TemporaryDirectory() as tmpdir:
            result = dispatch_agent_tool(
                "refresh_business_knowledge",
                {
                    "query": "TikTok Shop SEA phone case livestream trends",
                    "offline_results": [
                        {
                            "title": "SEA phone case livestream GMV rising",
                            "url": "https://example.com/phone-case",
                            "snippet": "Phone case livestream demand rises in Indonesia and Thailand.",
                        }
                    ],
                    "knowledge_dir": str(Path(tmpdir) / "knowledge"),
                    "memory_dir": str(Path(tmpdir) / "memory"),
                },
            )

            self.assertTrue(result["success"])
            self.assertTrue(Path(result["knowledge_path"]).exists())
            self.assertTrue(Path(result["memory_path"]).exists())
            memory = json.loads(Path(result["memory_path"]).read_text(encoding="utf-8"))
            self.assertIn("phone case", memory["summary"].lower())

    def test_content_generation_can_work_offline_and_points_to_xhs_skill(self):
        from backend.agent.registry import dispatch_agent_tool

        result = dispatch_agent_tool(
            "generate_marketing_content",
            {
                "product": "便携榨汁杯",
                "selling_points": ["USB 充电", "随身携带", "清洗方便"],
                "platform": "小红书",
                "offline": True,
            },
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["image_model"], "gpt-image-2")
        self.assertIn("小红书", result["copywriting"]["title"])
        self.assertIn("content-publishing", result["skill"])
        self.assertEqual(result["publish_status"], "manual_review_required")

    def test_media_api_tool_returns_permission_gated_acquisition_steps(self):
        from backend.agent.registry import dispatch_agent_tool

        result = dispatch_agent_tool(
            "inspect_media_api",
            {"platforms": ["巨量引擎", "聚光"], "capability": "RTA/RTB"},
        )

        self.assertTrue(result["success"])
        self.assertGreaterEqual(len(result["platforms"]), 2)
        for platform in result["platforms"]:
            self.assertIn("official_url", platform)
            self.assertIn("requires", platform)
            self.assertIn("next_steps", platform)

    def test_database_query_is_allowlisted_and_safe_when_supabase_missing(self):
        from backend.agent.registry import dispatch_agent_tool

        result = dispatch_agent_tool(
            "query_backend_database",
            {"resource": "budget_projects", "limit": 3, "env": {}},
        )

        self.assertIn("success", result)
        self.assertIn("resource", result)
        self.assertEqual(result["resource"], "budget_projects")
        self.assertNotIn("service_role", json.dumps(result).lower())


class AgentToolOrchestratorIntegrationTest(unittest.TestCase):
    def test_orchestrator_exposes_agent_tool_schemas(self):
        from backend import orchestrator

        schema_names = {tool["function"]["name"] for tool in orchestrator.ORCHESTRATOR_TOOLS}
        self.assertIn("allocate_budget", schema_names)
        self.assertIn("simulate_live_workbench", schema_names)
        self.assertIn("generate_marketing_content", schema_names)

    def test_runtime_prompt_includes_skills_and_tools_for_qiji_agent(self):
        from backend.agent.runtime import build_runtime_system_prompt

        prompt = build_runtime_system_prompt()

        self.assertIn("MaiDeal agent runtime", prompt)
        self.assertIn("allocate_budget", prompt)
        self.assertIn("content-publishing", prompt)
        self.assertIn("business-knowledge", prompt)


if __name__ == "__main__":
    unittest.main()
