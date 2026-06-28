import json
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]


class _FakeCompletions:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self.responses:
            raise AssertionError("unexpected extra model call")
        return self.responses.pop(0)


class _FakeOpenAIClient:
    def __init__(self, responses):
        self.chat = SimpleNamespace(completions=_FakeCompletions(responses))


def _completion(message):
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def _assistant_message(content=None, tool_calls=None):
    return SimpleNamespace(content=content, tool_calls=tool_calls or [])


def _tool_call(name, arguments):
    return SimpleNamespace(
        id="call_budget_1",
        type="function",
        function=SimpleNamespace(
            name=name,
            arguments=json.dumps(arguments, ensure_ascii=False),
        ),
    )


class AgentRuntimePromptTest(unittest.TestCase):
    def test_runtime_prompt_loads_full_skill_documents_and_filters(self):
        from backend.agent.runtime import build_runtime_system_prompt, load_skill_documents

        docs = load_skill_documents(skill_names=["content-publishing"])

        self.assertEqual(["content-publishing"], [doc["name"] for doc in docs])
        self.assertIn("Never claim that the content was posted", docs[0]["content"])

        prompt = build_runtime_system_prompt(
            skill_names=["content-publishing"],
            tool_names=["generate_marketing_content"],
        )

        self.assertIn("generate_marketing_content", prompt)
        self.assertIn("Never claim that the content was posted", prompt)
        self.assertNotIn("simulate_live_workbench", prompt)


class AgentRuntimeRunnerTest(unittest.IsolatedAsyncioTestCase):
    async def test_runtime_executes_multi_round_tool_calls_with_qiji_compatible_client(self):
        from backend.agent.runtime_runner import run_agent_runtime

        first_message = _assistant_message(
            tool_calls=[
                _tool_call(
                    "allocate_budget",
                    {
                        "total_budget": 1000,
                        "channels": [
                            {"id": "tiktok", "roi": 2.0, "min_budget": 100, "max_budget": 500},
                            {"id": "meta", "roi": 3.5, "min_budget": 100, "max_budget": 700},
                        ],
                    },
                )
            ],
        )
        second_message = _assistant_message(content="已完成预算分配，Meta 获得更多预算。")
        client = _FakeOpenAIClient([
            _completion(first_message),
            _completion(second_message),
        ])

        result = await run_agent_runtime(
            messages=[{"role": "user", "content": "帮我按 ROI 分配 1000 美元预算"}],
            config={"api_key": "test-key", "api_base": "https://api.openai-next.com/v1"},
            client=client,
            model="gpt-5",
            tool_names=["allocate_budget"],
            skill_names=["budget-allocation"],
        )

        self.assertTrue(result["success"])
        self.assertEqual("gpt-5", result["model"])
        self.assertEqual("已完成预算分配，Meta 获得更多预算。", result["output_text"])
        self.assertEqual(["allocate_budget"], [call["name"] for call in result["tool_calls"]])
        self.assertTrue(result["tool_results"][0]["result"]["success"])
        self.assertEqual(2, len(client.chat.completions.calls))
        self.assertEqual("gpt-5", client.chat.completions.calls[0]["model"])
        self.assertEqual("allocate_budget", client.chat.completions.calls[0]["tools"][0]["function"]["name"])
        self.assertTrue(any(message["role"] == "tool" for message in client.chat.completions.calls[1]["messages"]))


class AgentRuntimeApiTest(unittest.TestCase):
    def test_api_exposes_dedicated_agent_runtime_endpoint(self):
        source = (ROOT / "backend/api.py").read_text(encoding="utf-8")

        self.assertIn("/api/agent/runtime", source)
        self.assertIn("run_agent_runtime", source)
        self.assertIn("AgentRuntimeRequest", source)


if __name__ == "__main__":
    unittest.main()
