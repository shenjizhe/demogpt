import json
import os
import tempfile
from typing import Optional, List

from langchain.tools.render import render_text_description
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.prompts import load_prompt, BasePromptTemplate, PipelinePromptTemplate
from langchain_core.tools import BaseTool


def _load_file(filename):
    """ Loads a file into a string."""
    if not os.path.exists(filename):
        raise FileExistsError(f"File {filename} not found.")
    f = os.path.abspath(filename, "r", encoding="utf8")
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

    def build(
            self,
            tools: Optional[List[BaseTool]] = None,
            output_parser: Optional[BaseOutputParser] = None
    ) -> BasePromptTemplate:
        """ Builds a prompt template. from tools & output parser """

        main_file = os.path.join(self.prompt_path, self.prompt_file)
        main_prompt_template = load_prompt(
            self._check_or_redirect(main_file)
        )

        variables = main_prompt_template.input_variables
        partial_variables = {}
        recursive_templates = []

        # 遍历所有变量，检查是否存在对应的末班文件
        for var in variables:
            # 是否存在嵌套模板
            if os.path.exists(os.path.join(self.prompt_path, f"{var}.json")):
                sub_template = PromptTemplateBuilder(
                    self.prompt_path,
                    f"{var}.json"
                ).build(
                    tools=tools,
                    output_parser=output_parser
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

        if output_parser is not None and "format_instructions" in variables:
            partial_variables["format_instructions"] = _chinese_friendly(
                output_parser.format_instructions
            )

        if recursive_templates:
            main_prompt_template = PipelinePromptTemplate(
                final_prompt=main_prompt_template,
                pipeline_prompt=recursive_templates
            )

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
