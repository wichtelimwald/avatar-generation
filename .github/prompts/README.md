# Using Copilot Agents on GitHub.com

Invoke any agent in Copilot Chat by typing `@` followed by the agent name.

## Available Agents

All agent definitions live in `.github/agents/`. To invoke one, open
**Copilot Chat** on github.com and type:

```
@<agent-name> <your request>
```

For example:

```
@orchestrator Plan the implementation of the trip-sharing feature.
@code-review Review this PR for SOLID violations.
@geo-expert Design a clustering algorithm for nearby activities.
@tester Write unit tests for the Rating model.
```

## Agent List

See the **Agent Usage** table in
[`.github/copilot-instructions.md`](../copilot-instructions.md#agent-usage)
for the full list of agents and their responsibilities.

## Tips

- **Be specific:** Give the agent clear context — file paths, requirements, constraints.
- **One task per message:** Each agent works best with a focused request.
- **Chain agents:** Use `@orchestrator` to coordinate multi-agent workflows.
- **Self-management:** All agents follow the principles in
  `.github/agents/self-management.md` and produce a Session Summary at the end.
