import ast
import os
from collections import defaultdict


class CycleDetector:
    def __init__(self, root):
        self._root = os.path.abspath(root)
        self._dirs = set()

    def add_directory(self, directory):
        self._dirs.add(self._root+directory)

    @staticmethod
    def _find_imports(filepath):
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read())

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports

    @staticmethod
    def _detect_cycles(graph):
        visited = set()
        in_stack = set()
        cycles = []

        def dfs(node, path):
            visited.add(node)
            in_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in in_stack:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])

            path.pop()
            in_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    def _build_dependency_graph(self, project_path):
        graph = defaultdict(set)

        for root, dirs, files in os.walk(project_path):
            for f in files:
                if f.endswith('.py'):
                    filepath = os.path.join(root, f)
                    module = filepath.replace(self._root, '').replace('/', '.').replace('.py', '').lstrip('.')
                    imports = self._find_imports(filepath)
                    for imp in imports:
                        graph[module].add(imp)
        return graph

    def detect(self):
        graph = defaultdict(set)
        for directory in self._dirs:
            graph.update(self._build_dependency_graph(directory))
        return self._detect_cycles(graph)