# Agent team context policy

`context_policy` is required for every entry in `agents[]`. It controls only
the corresponding `spawn_agent` call and brief; it is not a Codex config key.

## Fields

- `fork_turns`: `"none"`, `"all"`, or a positive integer. `planner`,
  `reviewer`, `security`, and `qa` must use `"none"`. A `worker` may use
  `"none"` or an integer up to `3`; an integer requires `reason`. A worker may
  never use `"all"`.
- `model_tier`: `"explorer"`, `"reviewer"`, `"worker"`, or `"custom"`, matching
  the role templates under `codex/agents/`. `"custom"` also requires `model`
  and `model_reasoning_effort`.
- `allowed_skills`: skill names the agent may load. Defaults to `[]`.
- `allowed_mcp`: MCP names the agent may use. Defaults to `[]`.
- `upstream_inputs`: repo-relative paths to structured summaries produced by
  upstream agents. Defaults to `[]`.
- `reason`: required only when `fork_turns != "none"`.

When `upstream_inputs` is non-empty, the agent may not repeat any
`allowed_skills` declared by an earlier agent in `agents[]`. The list order is
therefore the upstream order for `ERROR[context_policy_reload]` checks.

Validate before rendering:

```bash
python3 scripts/harness_agent_team.py validate PLAN.json
python3 scripts/harness_agent_team.py brief PLAN.json --agent AGENT_ID
```

## Example: explorer and worker

```json
{
  "agents": [
    {
      "id": "explorer",
      "role": "planner",
      "scope": "Inspect the existing agent-team contract",
      "write_set": [],
      "verification_command": "python3 test_runner.py",
      "context_policy": {
        "fork_turns": "none",
        "model_tier": "explorer",
        "allowed_skills": ["research"],
        "allowed_mcp": [],
        "upstream_inputs": []
      }
    },
    {
      "id": "worker",
      "role": "worker",
      "scope": "Implement the validated agent-team change",
      "write_set": ["scripts/harness_agent_team.py"],
      "verification_command": "python3 test_runner.py",
      "task_demand": {
        "level": "low",
        "L": "One bounded CLI change",
        "H_tool": "Known Python CLI",
        "S_state": "One source file",
        "N_obs": "Deterministic JSON"
      },
      "green_gate": {
        "gate_scope": "worker",
        "command": "python3 test_runner.py",
        "rationale": "The repository runner covers the CLI contract"
      },
      "context_policy": {
        "fork_turns": 2,
        "model_tier": "worker",
        "allowed_skills": ["tdd"],
        "allowed_mcp": [],
        "upstream_inputs": [],
        "reason": "Two recent turns contain the accepted CLI seam"
      }
    }
  ]
}
```

## Example: three agents with an upstream summary

```json
{
  "agents": [
    {
      "id": "explorer",
      "role": "planner",
      "scope": "Inspect the current contract",
      "write_set": [],
      "verification_command": "python3 test_runner.py",
      "context_policy": {
        "fork_turns": "none",
        "model_tier": "explorer",
        "allowed_skills": ["research"],
        "allowed_mcp": [],
        "upstream_inputs": []
      }
    },
    {
      "id": "producer",
      "role": "worker",
      "scope": "Produce the structured upstream summary",
      "write_set": ["artifacts/structured-summary.json"],
      "verification_command": "python3 test_runner.py",
      "task_demand": {
        "level": "low",
        "L": "Summarize inspected findings",
        "H_tool": "Known local files",
        "S_state": "One summary artifact",
        "N_obs": "Deterministic input"
      },
      "green_gate": {
        "gate_scope": "worker",
        "command": "python3 test_runner.py",
        "rationale": "The repository runner covers the summary contract"
      },
      "context_policy": {
        "fork_turns": "none",
        "model_tier": "worker",
        "allowed_skills": ["analysis"],
        "allowed_mcp": ["filesystem"],
        "upstream_inputs": []
      }
    },
    {
      "id": "consumer",
      "role": "worker",
      "scope": "Consume the structured summary without reloading upstream skills",
      "write_set": ["scripts/harness_report.py"],
      "verification_command": "python3 test_runner.py",
      "task_demand": {
        "level": "low",
        "L": "One bounded consumer change",
        "H_tool": "Known Python CLI",
        "S_state": "One source file and one upstream summary",
        "N_obs": "Deterministic JSON"
      },
      "green_gate": {
        "gate_scope": "worker",
        "command": "python3 test_runner.py",
        "rationale": "The repository runner covers the consumer contract"
      },
      "context_policy": {
        "fork_turns": "none",
        "model_tier": "worker",
        "allowed_skills": ["tdd"],
        "allowed_mcp": [],
        "upstream_inputs": ["artifacts/structured-summary.json"]
      },
      "brief": {
        "category": "enhancement",
        "summary": "Consume a structured upstream summary.",
        "current_behavior": "The consumer does not use the structured summary.",
        "desired_behavior": "The consumer reads the summary without reloading upstream context.",
        "key_interfaces": ["scripts/harness_report.py CLI"],
        "acceptance_criteria": ["python3 test_runner.py passes"],
        "out_of_scope": ["Changing evidence schemas"]
      }
    }
  ]
}
```
