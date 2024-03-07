from typing import List, Optional

from langchain.memory import ConversationTokenBufferMemory, VectorStoreRetrieverMemory
from langchain.output_parsers import OutputFixingParser
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.tools import BaseTool
from langchain_core.vectorstores import VectorStoreRetriever

from AutoAgent.Action import Action
from Utils.PromptTemplateBuilder import PromptTemplateBuilder


class AutoGPT:
    def __init__(
            self,
            llm: BaseChatModel,
            prompts_path: str,
            tools: List[BaseTool],
            work_dir: str = "./data",
            main_prompt_file: str = "main_prompt.json",
            final_prompt_file: str = "final_step.json",
            max_thought_steps: Optional[int] = 10,
            memory_retriever: Optional[VectorStoreRetriever] = None,
    ):
        """initial the self values, i.e. self.xxx=xxx """
        self.llm = llm
        self.prompts_path = prompts_path
        self.tools = tools
        self.work_dir = work_dir
        self.main_prompt_file = main_prompt_file
        self.final_prompt_file = final_prompt_file
        self.max_thought_steps = max_thought_steps
        self.memory_retriever = memory_retriever

        # PydanticOutputParser ,如果输出格式不正确，则尝试修复
        self.output_parser = PydanticOutputParser(pydantic_object=Action)
        self.robust_parser = OutputFixingParser.from_llm(parser=self.output_parser, llm=self.llm)

    def run(self, task_description, verbose=False) -> str:
        thought_step_count = 0

        prompt_template = PromptTemplateBuilder(
            self.prompts_path,
            self.main_prompt_file,
        ).build(
            self.tools,
            self.output_parser,
        ).partial(
            work_dir=self.work_dir,
            task_description=self.task_description,
        )

        short_term_memory = ConversationTokenBufferMemory(
            llm=self.llm,
            max_token_limit=4000,
        )

        short_term_memory.save_context(
            {"input": "\n初始化"},
            {"output": "\n开始"}
        )

        chain = (prompt_template |
                 self.llm |
                 StrOutputParser())

        # 如果有长时记忆，那么加载长时记忆
        if self.memory_retriever is not None:
            long_term_memory = VectorStoreRetrieverMemory(
                retrievers=self.memory_retriever,
            )
        else:
            long_term_memory = None

        reply = ""

        while thought_step_count < self.max_thought_steps:
            action, response = self._step(
                chain,
                task_description=task_description,
                short_term_memory=short_term_memory,
                long_term_memory=long_term_memory,
                verbose=verbose,
            )

    # def _step(self, reason_chain, task_description, short_term_memory, long_term_memory, verbose):
    #
    #     response = ""
    #
    #     for reason_chain.stream({
    #         "short_term_memory": _format_short_term_memory(short_term_memory),
    #         "long_term_memory": _format_long_term_memory(task_description, long_term_memory)
    #         if long_term_memory is not None else "",
    #     }):
    #         if verbose:
    #             color_print(s,THOUGHT_COLOR, end="")
    #         response += s
    #
    #     action = robust_parser.parse(response)
    #     return action, response
