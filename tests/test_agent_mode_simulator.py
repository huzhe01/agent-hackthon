import unittest


class AgentModeSimulatorTest(unittest.TestCase):
    def test_simulator_generates_seeded_skus_channels_frames_and_review(self):
        from backend.agent_mode_simulator import build_simulation_bundle

        brief = {
            "budget": 5000,
            "target_roas": 3.0,
            "products": "便携榨汁杯",
            "market": "美国 / USD",
            "channels": "TikTok Ads, Meta Ads, Shopee Ads",
            "inventory": "1200 件",
            "margin": "55%",
        }

        first = build_simulation_bundle(brief, version_number=1)
        second = build_simulation_bundle(brief, version_number=1)

        self.assertEqual(first["simulator_seed"], second["simulator_seed"])
        self.assertEqual(first["product_catalog"], second["product_catalog"])
        self.assertEqual(len(first["product_catalog"]), 5)
        self.assertEqual(
            [pool["label"] for pool in first["channel_pools"]],
            ["TikTok Ads", "Meta Ads", "Shopee Ads"],
        )
        self.assertEqual(
            sum(pool["total"] for pool in first["channel_pools"]),
            5000,
        )
        self.assertEqual(len(first["plan_options"]), 3)
        self.assertEqual(
            [plan.get("recommended", False) for plan in first["plan_options"]],
            [False, True, False],
        )

        frames = first["live_demo"]["frames"]
        self.assertGreaterEqual(len(frames), 6)
        self.assertTrue(any(frame.get("alerts") for frame in frames))
        for frame in frames:
            metrics = frame["metrics"]
            sku_gmv = sum(item["gmv"] for item in frame["sku_ads"])
            spend = sum(pool["spent"] for pool in frame["budget_pool"])
            self.assertEqual(metrics["revenue"], sku_gmv)
            self.assertEqual(metrics["spend"], spend)
            if spend:
                self.assertAlmostEqual(metrics["roas"], round(sku_gmv / spend, 1))
            self.assertEqual(metrics["profit"], sku_gmv - spend)

        review = first["review"]
        final_metrics = frames[-1]["metrics"]
        self.assertEqual(review["actual_roas"], final_metrics["roas"])
        self.assertEqual(review["expected_roas"], 3.0)
        self.assertIn("api_trace", review)

    def test_simulator_requires_channels_before_plan_generation(self):
        from backend.agent_mode_simulator import validate_simulation_brief

        status = validate_simulation_brief({
            "budget": 5000,
            "target_roas": 3,
            "products": "手机壳",
            "market": "东南亚 / SGD",
        })

        self.assertFalse(status["complete"])
        self.assertIn("channels", status["missing"])


if __name__ == "__main__":
    unittest.main()
