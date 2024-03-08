#  Copyright 2021-2099 the original author or authors.
#
#  @File: FileTools.py
#  @Author: thirdlucky
#  @Date: 2024-03-08 13:34:36
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

import os


def list_files_in_directory(path: str) -> str:
    """List all file names in the directory"""
    file_names = os.listdir(path)

    # Join the file names into a single string, separated by a newline
    return "\n".join(file_names)
