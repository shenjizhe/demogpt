from typing import List, Optional

from langchain.memory import ConversationTokenBufferMemory, VectorStoreRetrieverMemory
from langchain.output_parsers import OutputFixingParser, PydanticOutputParser
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import BaseTool
from langchain_core.vectorstores import VectorStoreRetriever
from pydantic import ValidationError

from AutoAgent.Action import Action
from Utils.PrintUtils import color_print, THOUGHT_COLOR, ROUND_COLOR, OBSERVATION_COLOR
from Utils.PromptTemplateBuilder import PromptTemplateBuilder


def _format_short_term_memory(memory):
    """join the short term memory into a single string. from second message - first is a fake message"""
    messages = memory.chat_memory.messages
    string_messages = [messages[i].content for i in range(1, len(messages))]
    return "\n".join(string_messages)


def _format_long_term_memory(task_description, memory):
    """get string from memory of history key"""
    return memory.load_memory_variables({
        "prompt": task_description,
    })["history"]


class AutoGPT:
    """long chain agent"""

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

        # 如果有长时记忆，那么加载长时记忆
        if self.memory_retriever is not None:
            long_term_memory = VectorStoreRetrieverMemory(
                retrievers=self.memory_retriever,
            )
        else:
            long_term_memory = None

        prompt_template = PromptTemplateBuilder(
            self.prompts_path,
            self.main_prompt_file,
        ).build(
            tools=self.tools,
            output_parser=self.output_parser,
        ).partial(
            work_dir=self.work_dir,
            task_description=self.task_description,
            long_term_memory=_format_long_term_memory(task_description, long_term_memory)
            if long_term_memory is not None else "",

        )

        # 初始化短期记忆
        short_term_memory = ConversationTokenBufferMemory(
            llm=self.llm,
            max_token_limit=4000,
        )

        short_term_memory.save_context(
            {"input": "\n初始化"},
            {"output": "\n开始"}
        )

        chain = (prompt_template | self.llm | StrOutputParser())

        reply = ""

        while thought_step_count < self.max_thought_steps:
            if verbose:
                color_print(f">>>>round: {thought_step_count}<<<<", ROUND_COLOR)
            action, response = self._step(
                chain,
                short_term_memory=short_term_memory,
                verbose=verbose,
            )

            if action.name == "FINISH":
                if verbose:
                    color_print(f"\n-----\nfinish", OBSERVATION_COLOR)
                reply = self._final_step(short_term_memory, task_description)
                break

            observation = action._exec_action(action)

            if verbose:
                color_print(f"\n-----\n{observation}", OBSERVATION_COLOR)

            short_term_memory.save_context(
                {"input": response},
                {"output": "返回结果:\n" + observation}
            )

            thought_step_count += 1

            if not reply:
                reply = "抱歉，我没能完成你的任务"

            if long_term_memory is not None:
                long_term_memory.save_context(
                    {"input": task_description},
                    {"output": reply},
                )

        return reply

    def _step(self, reason_chain, short_term_memory, verbose):
        """ run a step get a short memory and parse an action """

        response = ""

        for s in reason_chain.stream({
            "short_term_memory": _format_short_term_memory(short_term_memory),
        }):
            if verbose:
                color_print(s, THOUGHT_COLOR, end="")
            response += s

        action = self.robust_parser.parse(response)
        return action, response

    def _exec_action(self, action):
        """查找工具，执行工具，并处理异常"""

        tool = self._find_tool(action.name)
        if tool is None:
            observation = (
                f"Error:找不到工具或指令{action.name}。"
                f"请从提供的工具或指令中选择，确保按照格式输出。"
            )
        else:
            try:
                observation = tool.run(action.args)
            except ValidationError as e:
                observation = (
                    f"Validation Error in args:{str(e)}, args:{action.args}"
                )
            except Exception as e:
                observation = (
                    f"Error:{str(e)},{type(e).__name__}, args:{action.args}"
                )
        return observation

    def _find_tool(self, name):
        """ find tool from tools by name """
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    def _final_step(self, short_term_memory, task_description):
        """生成最终提示词模板，然后组成 long chain expression language 并执行，最后返回结果"""
        final_prompt = PromptTemplateBuilder(
            self.prompts_path,
            self.final_prompt_file,
        ).build().partial(
            task_description=task_description,
            short_term_memory=_format_short_term_memory(short_term_memory),
        )
        chain = (final_prompt | self.llm | StrOutputParser())
        response = chain.invoke({})
        return response
