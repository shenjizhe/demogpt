#  Copyright 2021-2099 the original author or authors.
#
#  @File: PrintUtils.py
#  @Author: thirdlucky
#  @Date: 2024-03-07 15:02:07
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

import sys

from colorama import Fore, Style

THOUGHT_COLOR = Fore.GREEN
OBSERVATION_COLOR = Fore.YELLOW
ROUND_COLOR = Fore.BLUE
CODE_COLOR = Fore.WHITE


def color_print(text: str, color: str = None, end="\n"):
    if color is not None:
        content = color + text + Style.RESET_ALL + end
    else:
        content = text + end
    sys.stdout.write(content)
    sys.stdout.flush()
