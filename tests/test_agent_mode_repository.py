import unittest


class FakeSupabaseTransport:
    def __init__(self):
        self.projects = []
        self.plan_versions = []
        self.skus = []
        self.frames = []
        self.events = []
        self.actions = []
        self.reviews = []
        self.requests = []

    def request(self, method, path, *, params=None, json_body=None, prefer=None):
        self.requests.append({
            "method": method,
            "path": path,
            "params": params or {},
            "json": json_body,
            "prefer": prefer,
        })
        table_name = path.rsplit("/", 1)[-1]
        rows = getattr(self, _table_attr(table_name))

        if method == "GET":
            return rows
        if method == "POST":
            if isinstance(json_body, list):
                rows.extend(json_body)
                return json_body
            rows.append(json_body)
            return [json_body]
        if method == "PATCH":
            for row in rows:
                row.update(json_body or {})
            return rows
        raise AssertionError(f"Unexpected method {method}")


def _table_attr(table_name):
    return {
        "agent_budget_projects": "projects",
        "agent_plan_versions": "plan_versions",
        "agent_project_skus": "skus",
        "agent_live_frames": "frames",
        "agent_events": "events",
        "agent_live_actions": "actions",
        "agent_reviews": "reviews",
    }[table_name]


class AgentModeRepositoryTest(unittest.TestCase):
    def test_repository_persists_and_rehydrates_complete_project_snapshot(self):
        from backend.agent_mode_repository import AgentModeRepository
        from backend.agent_mode_simulator import build_simulation_bundle

        transport = FakeSupabaseTransport()
        repository = AgentModeRepository(transport=transport, tenant_key="demo")
        brief = {
            "budget": 3200,
            "target_roas": 2.8,
            "products": "磁吸手机壳",
            "market": "东南亚 / SGD",
            "channels": "TikTok Ads, Shopee Ads",
        }
        bundle = build_simulation_bundle(brief, version_number=1)

        saved = repository.save_generated_plan(brief, bundle)
        workbench = repository.build_workbench()

        self.assertEqual(saved["project"]["name"], "磁吸手机壳 · 东南亚直播")
        self.assertEqual(len(transport.projects), 1)
        self.assertEqual(len(transport.plan_versions), 1)
        self.assertEqual(len(transport.skus), 5)
        self.assertEqual(len(transport.frames), len(bundle["live_demo"]["frames"]))
        self.assertEqual(
            len(transport.events),
            sum(len(frame.get("events", [])) for frame in bundle["live_demo"]["frames"]),
        )
        self.assertEqual(len(transport.reviews), 1)
        self.assertEqual(workbench["active_project_id"], saved["project"]["id"])
        self.assertEqual(workbench["project"]["product"], "磁吸手机壳")
        self.assertEqual(len(workbench["budget_projects"]), 1)
        self.assertEqual(workbench["live_demo"]["tick_interval_ms"], 5000)
        self.assertEqual(len(workbench["live_demo"]["frames"]), len(bundle["live_demo"]["frames"]))
        self.assertEqual(workbench["review_benchmarks"][1]["title"], "MaiDeal 托管实际")

    def test_repository_reports_disabled_without_supabase_secret(self):
        from backend.agent_mode_repository import create_agent_mode_repository

        repository = create_agent_mode_repository(env={})

        self.assertFalse(repository.enabled)


if __name__ == "__main__":
    unittest.main()
