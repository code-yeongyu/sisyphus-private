from pathlib import Path

from ruamel.yaml import YAML

from sisyphus.utils.plan_types import WorkPlan


class PlanLoader:
    def __init__(self, plan_path: Path = Path("./ai-todolist.yaml")) -> None:
        self.plan_path = plan_path
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.default_flow_style = False

    def load(self) -> WorkPlan:
        if not self.plan_path.exists():
            raise FileNotFoundError(f"작업계획서를 찾을 수 없습니다: {self.plan_path}")

        with self.plan_path.open("r", encoding="utf-8") as f:
            data = self.yaml.load(f)

        return WorkPlan(**data)

    def save(self, plan: WorkPlan) -> None:
        data = plan.model_dump(mode="python")
        with self.plan_path.open("w", encoding="utf-8") as f:
            self.yaml.dump(data, f)
