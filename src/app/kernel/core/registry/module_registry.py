from typing import List
from ..module import BaseModule


class ModuleRegistry:
    def __init__(self):
        self.modules: List[BaseModule] = []

    def register(self, module: BaseModule):
        self.modules.append(module)

    def get_all(self) -> List[BaseModule]:
        return self.modules
