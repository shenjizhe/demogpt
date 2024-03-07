import json
import os
import tempfile
from typing import Optional, List

from langchain.tools.render import render_text_description
from langchain_core.output_parsers import BaseOutputParser, PydanticOutputParser
from langchain_core.prompts import load_prompt, BasePromptTemplate, PipelinePromptTemplate
from langchain_core.tools import BaseTool, Tool

from AutoAgent.Action import Action


def _load_file(filename):
    """ Loads a file into a string."""
    if not os.path.exists(filename):
        raise FileExistsError(f"File {filename} not found.")
    f = open(filename, 'r', encoding='utf-8')
    s = f.read()
    f.close()
    return s


def _chinese_friendly(param):
    """ make sure that you can't transfer chinese char to 0xxxx """
    lines = param.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("{") and line.endswith("}"):
            try:
                lines[i] = json.dumps(json.loads(line), ensure_ascii=False)
            except:
                pass
    return "\n".join(lines)


class PromptTemplateBuilder:
    def __init__(self,
                 prompt_path: str,
                 prompt_file: str):
        self.prompt_path = prompt_path
        self.prompt_file = prompt_file

    def _check_or_redirect(self, prompt_file):
        """ if you use a relative path, it will be redirected to an absolute path"""

        with open(prompt_file, 'r', encoding="utf-8") as f:
            config = json.load(f)
        if "template_path" in config:
            # 如果是相对路径，则转换为绝对路径
            if not os.path.isabs(config["template_path"]):
                config["template_path"] = os.path.join(
                    self.prompt_path,
                    config["template_path"])
                # 生成临时文件
                tmp_file = tempfile.NamedTemporaryFile(
                    suffix=".json",
                    mode="w",
                    encoding="utf-8",
                    delete=False)
                tmp_file.write(json.dumps(config, ensure_ascii=False))
                tmp_file.close()
                return tmp_file.name
        return prompt_file

    def build(
            self,
            tools: Optional[List[BaseTool]] = None,
            parser: Optional[BaseOutputParser] = None
    ) -> BasePromptTemplate:
        """ Builds a prompt template. from tools & output parser """

        main_file = os.path.join(self.prompt_path, self.prompt_file)
        main_prompt_template = load_prompt(
            self._check_or_redirect(main_file)
        )

        variables = main_prompt_template.input_variables
        partial_variables = {}
        recursive_templates = []

        # 遍历所有变量，检查是否存在对应的模板文件
        for var in variables:
            # 是否存在嵌套模板
            if os.path.exists(os.path.join(self.prompt_path, f"{var}.json")):
                sub_template = PromptTemplateBuilder(
                    self.prompt_path,
                    f"{var}.json"
                ).build(
                    tools=tools,
                    parser=parser
                )
                recursive_templates.append(var, sub_template)
            elif os.path.exists(os.path.join(self.prompt_path, f"{var}.txt")):
                var_str = _load_file(
                    os.path.join(self.prompt_path, f"{var}.txt")
                )
                partial_variables[var] = var_str

        if tools is not None and "tools" in variables:
            tools_prompt = render_text_description(tools)
            partial_variables["tools"] = tools_prompt

        if parser is not None and "format_instructions" in variables:
            partial_variables["format_instructions"] = _chinese_friendly(
                parser.get_format_instructions()
            )

        if recursive_templates:
            main_prompt_template = PipelinePromptTemplate(
                final_prompt=main_prompt_template,
                pipeline_prompt=recursive_templates
            )
        # 将有值的变量填充到模板中
        main_prompt_template = main_prompt_template.partial(**partial_variables)

        return main_prompt_template


if __name__ == "__main__":
    builder = PromptTemplateBuilder("../prompts/main", "main.json")
    output_parser = PydanticOutputParser(pydantic_object=Action)
    prompt_template = builder.build(tools=[
        Tool(name="FINISH", func=lambda: None, description="任务完成")
    ], parser=output_parser)
    print(prompt_template.format(
        task_description="解决问题",
        work_dir=".",
        short_term_memory="",
        long_term_memory="",
    ))
