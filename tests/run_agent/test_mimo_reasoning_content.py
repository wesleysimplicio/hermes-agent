"""Tests for MiMo reasoning_content echo-back detection (#24443)."""

from run_agent import AIAgent


def _make_agent(base_url="", model="", provider="openai"):
    agent = object.__new__(AIAgent)
    agent.base_url = base_url
    agent.model = model
    agent.provider = provider
    return agent


def test_mimo_url_triggers_pad():
    agent = _make_agent(base_url="https://api.xiaomimimo.com/v1")
    assert agent._needs_mimo_tool_reasoning() is True
    assert agent._needs_thinking_reasoning_pad() is True


def test_mimo_model_name_triggers_pad():
    agent = _make_agent(model="mimo-v2.5-pro")
    assert agent._needs_mimo_tool_reasoning() is True
    assert agent._needs_thinking_reasoning_pad() is True


def test_non_mimo_unaffected():
    agent = _make_agent(base_url="https://api.openai.com", model="gpt-4o")
    assert agent._needs_mimo_tool_reasoning() is False
    assert agent._needs_thinking_reasoning_pad() is False
