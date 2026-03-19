# agent-skills

This repo contains skills for three related systems that are often used together in an evaluation workflow:

- `Ground Truth Curator` (GTC): manages ground truth datasets and review workflows used to create and maintain evaluation inputs.
- `AML Evaluation Runner`: runs evaluation pipelines in Azure Machine Learning, including model inference, scoring, and optional publishing of results.
- `Experiment Catalog`: stores projects, experiments, permutations, and evaluation results so runs can be explored and compared.

The skills are organized in the same order the tools are typically used:

- `gtc-install`: installs and runs Ground Truth Curator locally or in Azure.
- `gtc-demo-data`: generates sample data for Ground Truth Curator, especially for queue and request-more workflows.
- `aml-eval-runner-install`: installs and configures the AML Evaluation Runner and its supporting Azure resources.
- `aml-eval-runner-demo`: sets up demo inference and evaluation modules and runs an end-to-end sample pipeline.
- `experiment-catalog-install`: deploys the Experiment Catalog locally or in Azure.
- `experiment-catalog-demo-data`: generates realistic demo projects, experiments, permutations, metrics, and results for the catalog.

## Deploying these skills

These skills use the GitHub skill layout, so the main deployment model is to place them under `.github/skills/` in the repository where the agent will run. In practice, that usually means copying or syncing the skill folders from this repo into the target repo's `.github/skills` directory.

They are most reliable on agent platforms that can do three things well: read repository-scoped instructions, execute shell commands, and handle long-running multi-step workflows. If a platform supports those patterns, these skills can usually be adapted even if it does not use GitHub's skill format natively.

Popular platform options:

- `GitHub Copilot CLI` (recommended): the best fit for these skills when you want interactive, multi-step execution, especially for infrastructure, local setup, Azure auth, and long-running validation steps.
- `VS Code with Copilot`: a good option if you want an editor-driven workflow and want the skills available while you inspect code or make manual changes alongside the agent.
- `GitHub Copilot coding agent` or PR-based workflows: useful when you want the agent to make repository changes in a branch or pull request, but less ideal for interactive deployment flows that require live credentials, prompts, or environment checks.
- `Claude Code` and similar terminal-first coding agents: often a good fit when they can read repo instructions and operate from the local checkout, especially for shell-heavy setup and troubleshooting flows.
- Other agentic IDEs or coding assistants, such as `Cursor` or comparable tools: potentially workable if they support repo-level guidance and reliable tool use, but they may need more manual adaptation than Copilot CLI.

Common deployment patterns:

- Keep the skills directly in the application or infrastructure repo if one team uses them in one main codebase.
- Keep them in a dedicated shared repo, then sync them into multiple target repos if several teams or projects need the same skills.
- Use a fork or internal mirror if you want to customize the prompts, references, or defaults for your own environment.

For these particular skills, `GitHub Copilot CLI` is still the strongest default because the workflows often involve multiple repos, shell commands, cloud resources, and handoffs between sub-agents. Platforms like `Claude Code` can also be a strong fit when you want a terminal-first experience, but you may need to adapt how the skills are surfaced if the platform does not natively consume `.github/skills`.

## Improving your results

Using any of these skills on its own should work well. For more complex scenarios, though—such as installing all three systems, sharing infrastructure, deploying inference and evaluation together, generating ground truth, running evaluations, and then viewing results in the catalog—there can be dozens or even hundreds of coordinated steps. That increases the chance of exhausting the model's context window, which can reduce reliability. A few practices can help:

- Use a Research, Plan, Implement (RPI) pattern. It gives the agent space to study the skills, the underlying repos, and your request, then build a step-by-step plan before making changes. You can find good RPI agents here: <https://github.com/microsoft/hve-core>.

- Use Copilot CLI instead of Copilot Chat in VS Code. In my testing, it followed the skills more consistently, including better use of sub-agents, and used less context overall.

- Use the most capable models available. I tested with Claude Opus 4.6 and GPT-5.4 and got good results.

- Be specific about what you want to achieve, and ask the agent to summarize what it did at the end so you can verify the result.
