from typing import Any, List, Optional, Union

from ....base import BaseComponent
from ....llms import PromptTemplate
from ..base import BaseLLM, BaseTool
from ..output.base import BaseScratchPad
from .prompt import zero_shot_planner_prompt


class Planner(BaseComponent):
    model: BaseLLM
    prompt_template: Optional[PromptTemplate] = None
    examples: Optional[Union[str, List[str]]] = None
    plugins: List[BaseTool]

    def _compose_worker_description(self) -> str:
        """
        Compose the worker prompt from the workers.

        Example:
        toolname1[input]: tool1 description
        toolname2[input]: tool2 description
        """
        prompt = ""
        try:
            for worker in self.plugins:
                prompt += f"{worker.name}[input]: {worker.description}\n"
        except Exception:
            raise ValueError("Worker must have a name and description.")
        return prompt

    def _compose_fewshot_prompt(self) -> str:
        if self.examples is None:
            return ""
        if isinstance(self.examples, str):
            return self.examples
        else:
            return "\n\n".join([e.strip("\n") for e in self.examples])

    def _compose_prompt(self, instruction) -> str:
        """
        Compose the prompt from template, worker description, examples and instruction.
        """
        worker_desctription = self._compose_worker_description()
        fewshot = self._compose_fewshot_prompt()
        if self.prompt_template is not None:
            if "fewshot" in self.prompt_template.placeholders:
                return self.prompt_template.populate(
                    tool_description=worker_desctription,
                    fewshot=fewshot,
                    task=instruction,
                )
            else:
                return self.prompt_template.populate(
                    tool_description=worker_desctription, task=instruction
                )
        else:
            if self.examples is not None:
                return zero_shot_planner_prompt.populate(
                    tool_description=worker_desctription,
                    fewshot=fewshot,
                    task=instruction,
                )
            else:
                return zero_shot_planner_prompt.populate(
                    tool_description=worker_desctription, task=instruction
                )

    def run(self, instruction: str, output: BaseScratchPad = BaseScratchPad()) -> Any:
        response = None
        output.info("Running Planner")
        prompt = self._compose_prompt(instruction)
        output.debug(f"Prompt: {prompt}")
        try:
            response = self.model(prompt)
            output.info("Planner run successful.")
        except ValueError as e:
            output.error("Planner failed to retrieve response from LLM")
            raise ValueError("Planner failed to retrieve response from LLM") from e

        return response
