"""Validate the maintained team configuration without changing any files."""
from pathlib import Path
import ast
import json
import tomllib

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = {
    "fullstack-agent": "gpt-6.1-sol",
    "coding-agent": "gpt-6.1-sol",
    "devops-agent": "gpt-6.1-sol",
    "review-agent": "gpt-6-astra",
    "sa-agent": "gpt-6-astra",
}
config = tomllib.loads((ROOT / ".codex/config.toml").read_text(encoding="utf-8"))
assert config["model"] == "gpt-6.1-sol"
assert config["agents"] == {"max_concurrent_threads_per_session": 3, "max_depth": 1}
assert config["plugins"]["codex-agent-team@creep-local"]["enabled"] is True
assert not {"model_provider", "sandbox_mode"} & config.keys()
assert config["approval_policy"] == "on-request"
assert config["approvals_reviewer"] == "user"
assert config["features"]["apps"] is False
assert config["apps"]["_default"] == {
    "enabled": False, "approvals_reviewer": "user", "default_tools_approval_mode": "prompt",
}
assert config["mcp_servers"]["playwright"]["args"] == ["@playwright/mcp@0.0.70"]
assert all(server["enabled"] is False and server["default_tools_approval_mode"] == "prompt"
           for server in config["mcp_servers"].values())
assert "@latest" not in (ROOT / ".codex/config.toml").read_text(encoding="utf-8")
for path in ROOT.rglob("*.toml"):
    if ".git" not in path.parts:
        tomllib.loads(path.read_text(encoding="utf-8"))
for path in ROOT.rglob("*.json"):
    if ".git" not in path.parts:
        json.loads(path.read_text(encoding="utf-8"))
assert {p.stem for p in (ROOT / ".codex/agents").glob("*.toml")} == EXPECTED.keys()
for role, model in EXPECTED.items():
    agent = tomllib.loads((ROOT / f".codex/agents/{role}.toml").read_text(encoding="utf-8"))
    assert agent["name"] == role and agent["model"] == model
    assert agent["model_reasoning_effort"] == "high"
    assert agent["developer_instructions"].strip()
market = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
assert market["name"] == "creep-local"
plugin = ROOT / market["plugins"][0]["source"]["path"]
manifest = json.loads((plugin / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
assert manifest["name"] == "codex-agent-team"
assert not {"hooks", "mcpServers", "apps"} & manifest.keys()
skills = plugin / manifest["skills"]
assert {p.name for p in skills.iterdir()} == {
    "team-brainstorm", "team-coordination", "team-spec-workflow",
    "team-review-cycle", "team-documentation", "git-workflow",
}
for skill in skills.iterdir():
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n") and f"name: {skill.name}\n" in text
    assert "description:" in text.split("---", 2)[1]
    assert "aws-security-guidelines" not in text and "superpowers:" not in text
    assert (skill / "agents/openai.yaml").is_file()
assert not (ROOT / ".codex/hooks.json").exists()
assert not (ROOT / ".codex/hooks").exists()
rules = (ROOT / ".codex/rules/codex-agent-team.rules").read_text(encoding="utf-8")
tree = ast.parse(rules)
for node in tree.body:
    assert isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
    call = node.value
    assert isinstance(call.func, ast.Name) and call.func.id == "prefix_rule"
    values = {kw.arg: ast.literal_eval(kw.value) for kw in call.keywords}
    assert values["decision"] in {"prompt", "forbidden"}
    assert values["pattern"][0] in {"git", "docker"}
assert not (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines().count(".codex/")
print("PASS: TOML/JSON, model matrix, role files, plugin paths, skill metadata presence, rule structure, hooks omitted, specs versionable")
print("Runtime discovery and execution require separate client evidence; this script is static validation only.")
