import ast
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("app.services.analysis.ast_analyzer")

class ASTVisitor(ast.NodeVisitor):
    def __init__(self):
        self.functions: List[Dict[str, Any]] = []
        self.classes: List[Dict[str, Any]] = []
        self.imports: List[str] = []
        
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None

    def visit_Import(self, node: ast.Import):
        for name_alias in node.names:
            self.imports.append(name_alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for name_alias in node.names:
            full_name = f"{module}.{name_alias.name}" if module else name_alias.name
            self.imports.append(full_name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        prev_class = self.current_class
        self.current_class = node.name
        
        self.classes.append({
            "name": node.name,
            "start_line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno)
        })
        
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.visit_any_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.visit_any_function(node)

    def visit_any_function(self, node: Any):
        prev_function = self.current_function
        self.current_function = node.name
        
        # Statically scan call tokens inside this function definition
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
                    
        self.functions.append({
            "name": node.name,
            "class_name": self.current_class,
            "start_line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno),
            "calls": list(set(calls))
        })
        
        self.generic_visit(node)
        self.current_function = prev_function

def analyze_source_ast(source_code: str) -> Dict[str, Any]:
    """
    Parses a python source file using the standard ast module.
    Returns dictionaries of classes, functions, imports.
    If parsing fails due to syntax error, returns empty placeholders gracefully.
    """
    try:
        tree = ast.parse(source_code)
        visitor = ASTVisitor()
        visitor.visit(tree)
        return {
            "classes": visitor.classes,
            "functions": visitor.functions,
            "imports": list(set(visitor.imports))
        }
    except SyntaxError as e:
        logger.warning(f"AST Parsing syntax error: {e}")
        return {
            "classes": [],
            "functions": [],
            "imports": [],
            "error": f"SyntaxError: {e.msg} at line {e.lineno}"
        }
    except Exception as e:
        logger.error(f"AST Parsing unexpected failure: {e}")
        return {
            "classes": [],
            "functions": [],
            "imports": [],
            "error": str(e)
        }
