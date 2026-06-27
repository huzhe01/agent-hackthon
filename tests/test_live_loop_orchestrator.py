import importlib
import unittest


class LiveLoopOrchestratorTest(unittest.TestCase):
    def setUp(self):
        self.store = importlib.import_module("backend.agent_mode_store")
        importlib.reload(self.store)
        self.orchestrator = importlib.import_module("backend.orchestrator")
        importlib.reload(self.orchestrator)
        self.store.reset_workbench()
        self.store.write_workbench({
            "phase": "live",
            "project": {
                "product": "便携榨汁杯",
                "market": "美国 / USD",
                "totalBudget": "$5,000",
                "totalBudgetValue": 5000,
                "liveWindow": "20:00-23:00",
                "inventory": "1,200 件",
                "margin": "55%",
                "targetRoas": "3.0",
                "channels": "TikTok + Meta",
            },
            "selected_plan": "balanced",
            "guard_limit": "15",
            "approval_threshold": "800",
            "live_rooms": [
                {
                    "id": "creator",
                    "name": "直播间 A · 达人实测",
                    "budget": 1700,
                    "spent": 1180,
                    "channel": "TikTok 70% / Meta 30%",
                    "status": "投放中",
                    "roas": "2.4",
                },
                {
                    "id": "brand",
                    "name": "直播间 B · 品牌自播",
                    "budget": 2100,
                    "spent": 1000,
                    "channel": "TikTok 50% / Meta 50%",
                    "status": "投放中",
                    "roas": "3.5",
                },
            ],
        })

    def test_live_iteration_auto_executes_inside_guardrails(self):
        result, events = self.orchestrator._handle_run_live_iteration({"scenario": "auto"})

        self.assertTrue(result["success"])
        self.assertEqual(result["mode"], "auto_executed")
        self.assertTrue(any(event["type"] == "workbench_patch" for event in events))

        workbench = self.store.read_workbench()
        live_loop = workbench["live_loop"]
        self.assertEqual(live_loop["status"], "completed")
        self.assertIsNone(live_loop["pending_action"])
        self.assertEqual(
            [step["id"] for step in live_loop["steps"]],
            ["signal", "analysis", "planning", "orchestrator", "delivery", "verification"],
        )
        self.assertEqual(live_loop["steps"][4]["status"], "done")
        self.assertIn("验证", live_loop["verification"]["summary"])
        self.assertTrue(any("自动执行" in event["text"] for event in workbench["managed_events"]))

    def test_live_iteration_over_guardrails_waits_for_approval(self):
        result, _events = self.orchestrator._handle_run_live_iteration({"scenario": "high_risk"})

        self.assertTrue(result["success"])
        self.assertEqual(result["mode"], "pending_approval")

        workbench = self.store.read_workbench()
        live_loop = workbench["live_loop"]
        self.assertEqual(live_loop["status"], "pending_approval")
        self.assertIsNotNone(live_loop["pending_action"])
        self.assertTrue(live_loop["pending_action"]["requires_approval"])
        self.assertGreater(live_loop["pending_action"]["amount"], 800)
        self.assertEqual(live_loop["steps"][4]["status"], "waiting")

    def test_approve_live_action_executes_pending_action_and_verifies(self):
        self.orchestrator._handle_run_live_iteration({"scenario": "high_risk"})
        pending = self.store.read_workbench()["live_loop"]["pending_action"]

        result, _events = self.orchestrator._handle_approve_live_action({"action_id": pending["id"]})

        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "completed")

        workbench = self.store.read_workbench()
        live_loop = workbench["live_loop"]
        self.assertEqual(live_loop["status"], "completed")
        self.assertIsNone(live_loop["pending_action"])
        self.assertEqual(live_loop["last_action"]["status"], "executed")
        self.assertEqual(live_loop["steps"][4]["status"], "done")
        self.assertEqual(live_loop["steps"][5]["status"], "done")
        self.assertTrue(any("批准执行" in event["text"] for event in workbench["managed_events"]))

    def test_reject_live_action_records_constraint_and_replan(self):
        self.orchestrator._handle_run_live_iteration({"scenario": "high_risk"})
        pending = self.store.read_workbench()["live_loop"]["pending_action"]

        result, _events = self.orchestrator._handle_reject_live_action({
            "action_id": pending["id"],
            "reason": "不希望追加高风险预算",
        })

        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "rejected")

        workbench = self.store.read_workbench()
        live_loop = workbench["live_loop"]
        self.assertEqual(live_loop["status"], "rejected")
        self.assertIsNone(live_loop["pending_action"])
        self.assertEqual(live_loop["last_action"]["status"], "rejected")
        self.assertTrue(any("保守替代策略" in step["summary"] for step in live_loop["steps"]))
        self.assertTrue(any("已拒绝" in event["text"] for event in workbench["managed_events"]))

    def test_direct_live_command_router_maps_button_text_to_tools(self):
        self.orchestrator._handle_run_live_iteration({"scenario": "high_risk"})
        workbench = self.store.read_workbench()

        self.assertEqual(
            self.orchestrator._match_direct_live_command("运行一轮投中巡检", workbench),
            ("run_live_iteration", {"scenario": "auto"}),
        )
        self.assertEqual(
            self.orchestrator._match_direct_live_command("模拟高风险动作", workbench),
            ("run_live_iteration", {"scenario": "high_risk"}),
        )
        self.assertEqual(
            self.orchestrator._match_direct_live_command("批准执行当前待审批动作", workbench)[0],
            "approve_live_action",
        )
        self.assertEqual(
            self.orchestrator._match_direct_live_command("拒绝当前待审批动作，并重算", workbench)[0],
            "reject_live_action",
        )

    def test_direct_plan_command_updates_brief_and_generates_constrained_plans(self):
        self.store.write_workbench({
            "brief_fields": {
                "products": "便携榨汁杯",
                "target_roas": 3.0,
                "market": "美国 / USD",
            },
            "project": {
                "product": "便携榨汁杯",
                "targetRoas": "3.0",
                "market": "美国 / USD",
            },
        })
        workbench = self.store.read_workbench()

        self.assertEqual(
            self.orchestrator._match_direct_plan_command(
                "把这场直播的总预算改成 8,000 美元，Meta 最多占 45%，重新给我三套方案",
                workbench,
            ),
            (
                "extract_and_generate_plans",
                {"text": "把这场直播的总预算改成 8,000 美元，Meta 最多占 45%，重新给我三套方案"},
            ),
        )

        result, events = self.orchestrator._handle_extract_and_generate_plans({
            "text": "把这场直播的总预算改成 8,000 美元，Meta 最多占 45%，重新给我三套方案",
        })

        self.assertTrue(result["success"])
        self.assertEqual(result["mode"], "generated")
        self.assertTrue(any(event["type"] == "workbench_patch" for event in events))

        workbench = self.store.read_workbench()
        self.assertEqual(workbench["phase"], "planning")
        self.assertEqual(workbench["brief_fields"]["budget"], 8000)
        self.assertEqual(workbench["brief_fields"]["channels"], "TikTok + Meta")
        self.assertEqual(workbench["brief_fields"]["constraints"], "Meta 最多占 45%")
        self.assertEqual(len(workbench["plan_options"]), 3)
        self.assertEqual(len(workbench["plan_versions"]), 1)
        self.assertEqual(workbench["plan_versions"][0]["label"], "Plan v1")
        self.assertTrue(workbench["plan_versions"][0]["active"])
        self.assertEqual(
            [plan.get("recommended", False) for plan in workbench["plan_options"]],
            [False, True, False],
        )
        self.assertTrue(next(room for room in workbench["live_rooms"] if room["id"] == "brand")["recommended"])
        plan_text = "\n".join("\n".join(plan["lines"]) for plan in workbench["plan_options"])
        self.assertIn("Meta 45%", plan_text)
        self.assertNotIn("Meta 60%", plan_text)
        room_text = "\n".join(room["channel"] for room in workbench["live_rooms"])
        self.assertIn("Meta 45%", room_text)
        self.assertNotIn("Meta 60%", room_text)

        second_result, _second_events = self.orchestrator._handle_generate_plans({
            "brief_summary": "再次生成",
        })
        self.assertTrue(second_result["success"])
        versions = self.store.read_workbench()["plan_versions"]
        self.assertEqual([version["label"] for version in versions], ["Plan v1", "Plan v2"])
        self.assertFalse(versions[0]["active"])
        self.assertTrue(versions[1]["active"])

    def test_extract_brief_has_deterministic_followup_when_core_fields_missing(self):
        result, _events = self.orchestrator._handle_extract_brief({
            "budget": 8000,
            "constraints": "Meta 最多占 45%",
        })

        self.assertTrue(result["success"])
        self.assertIn("message", result)
        self.assertIn("还缺少", result["message"])
        self.assertIn("投放商品", result["message"])


if __name__ == "__main__":
    unittest.main()
