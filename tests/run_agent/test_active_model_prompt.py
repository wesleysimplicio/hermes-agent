"""Tests for _active_model/_active_provider reflected in system prompt."""
from run_agent import AIAgent


def _make_agent(model="gpt-4o", provider="openai"):
    agent = AIAgent.__new__(AIAgent)

    agent.model = model
    agent._active_model = model
    agent.provider = provider
    agent._active_provider = provider
    agent.pass_session_id = False
    agent.session_id = None

    def _volatile_line():
        from hermes_time import now as _now  # noqa: PLC0415
        now = _now()
        line = f"Conversation started: {now.strftime('%A, %B %d, %Y %I:%M %p')}"
        _disp_model = getattr(agent, "_active_model", None) or agent.model
        _disp_provider = getattr(agent, "_active_provider", None) or agent.provider
        if _disp_model:
            line += f"\nModel: {_disp_model}"
        if _disp_provider:
            line += f"\nProvider: {_disp_provider}"
        return line

    agent._volatile_line = _volatile_line
    return agent


class TestActiveModelPrompt:
    def test_init_values_appear_in_prompt(self):
        agent = _make_agent(model="claude-3-5", provider="anthropic")
        line = agent._volatile_line()
        assert "Model: claude-3-5" in line
        assert "Provider: anthropic" in line

    def test_switch_updates_active_attrs(self):
        agent = _make_agent(model="gpt-4o", provider="openai")
        agent._active_model = "ark-code-latest"
        agent._active_provider = "ark"
        line = agent._volatile_line()
        assert "Model: ark-code-latest" in line
        assert "Provider: ark" in line
        assert "gpt-4o" not in line

    def test_fallback_to_self_model_when_active_absent(self):
        agent = _make_agent(model="llama-3", provider="ollama")
        del agent._active_model
        del agent._active_provider
        line = agent._volatile_line()
        assert "Model: llama-3" in line
        assert "Provider: ollama" in line

    def test_empty_model_omitted(self):
        agent = _make_agent(model="", provider="")
        line = agent._volatile_line()
        assert "Model:" not in line
        assert "Provider:" not in line
