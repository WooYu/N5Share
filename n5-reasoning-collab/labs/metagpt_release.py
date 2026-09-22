"""MetaGPT SOP example; use a separate Python 3.11 environment. No LLM calls.

Official Action / Role / Team API checked. Runtime NOT verified on this Python 3.13 host.
"""
import asyncio
import json
import sys
from metagpt.actions import Action, UserRequirement
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team
from common import collect_reports, evaluate, sample, show


class CheckRelease(Action):
    name: str = "CheckRelease"

    async def run(self, source: dict) -> str:
        return json.dumps({"source": source, "reports": collect_reports(source)}, ensure_ascii=False)


class PublishReport(Action):
    name: str = "PublishReport"

    async def run(self, artifact: str, target: dict) -> str:
        data = json.loads(artifact)
        if data["source"] != target:
            raise ValueError("Artifact cannot replace the original task input")
        return json.dumps(evaluate(data["reports"], target), ensure_ascii=False)


class ReleaseReviewer(Role):
    name: str = "Reviewer"
    profile: str = "ReleaseReviewer"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([CheckRelease])
        self._watch([UserRequirement])

    async def _act(self) -> Message:
        source = json.loads(self.rc.news[-1].content)
        artifact = await self.rc.todo.run(source)
        return Message(content=artifact, role=self.profile, cause_by=type(self.rc.todo))


class ReportWriter(Role):
    name: str = "Writer"
    profile: str = "ReportWriter"
    target: dict

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([PublishReport])
        self._watch([CheckRelease])

    async def _act(self) -> Message:
        result = await self.rc.todo.run(self.rc.news[-1].content, self.target)
        show(json.loads(result))
        return Message(content=result, role=self.profile, cause_by=type(self.rc.todo))


async def main():
    target = sample(sys.argv[1] if len(sys.argv) > 1 else "blocked")
    team = Team()
    team.hire([ReleaseReviewer(), ReportWriter(target=target)])
    team.run_project(json.dumps(target))
    await team.run(n_round=3)


if __name__ == "__main__":
    asyncio.run(main())
