#  Copyright 2021-2099 the original author or authors.
#
#  @File: ExcelTool.py
#  @Author: thirdlucky
#  @Date: 2024-03-08 14:26:34
#  @Email: thirdlucky@126.com
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


# !pip install openpyxl
import pandas as pd

from Utils.PrintUtils import color_print


def get_sheet_names(
        file_name: str,
) -> str:
    """取得excel中所有表的名称"""
    excel_file = pd.ExcelFile(file_name)
    sheet_names = excel_file.sheet_names
    return f"这是 '{file_name}' 文件的工作表名称：\n\n{sheet_names}"


def get_column_names(
        file_name: str,
        sheet_index: int = 0,
) -> str:
    """取得excel中所有列的名称"""
    df = pd.read_excel(file_name, sheet_name=sheet_index)
    column_names = '\n'.join(
        df.columns.tolist()
    )

    result = f"这是 '{file_name}' 文件的第 {sheet_index} 个工作表的列名称：\n\n{column_names}"
    return result


def get_first_n_rows(
        file_name,
        sheet_index: int = 0,
        n: int = 3,
) -> str:
    """获取excel 文件中表格的前n行数据"""
    result = get_sheet_names(file_name) + "\n\n"
    result += get_column_names(file_name, sheet_index) + "\n\n"

    df = pd.read_excel(file_name, sheet_name=sheet_index)

    n_lines = "\n".join(
        df.head(n).to_string(index=False, header=True).split("\n")
    )

    result += f"这是 '{file_name}' 文件的第 {sheet_index} 个工作表的前 {n} 行数据：\n\n{n_lines}"

    return result


if __name__ == '__main__':
    file_name = "../data/供应商名录.xlsx"
    color_print(get_sheet_names(file_name))
    color_print(get_column_names(file_name))
    color_print(get_first_n_rows(file_name))
    color_print(get_first_n_rows(file_name, n=5))
