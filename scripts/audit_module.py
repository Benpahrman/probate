"""Module Authenticity & Completeness Forensic Scanner.

CLI utility to inspect any Python module or package against:
1. Completeness: Abstract methods, NotImplementedError, bare except, typing.
2. Usefulness & Wiring: Inbound import references across codebase.
3. Simulated vs Real-World: Detection of synthetic names ('Vance'), fake deeds,
   fake phone numbers ('555-'), deterministic hash modulo, random generators.
4. I/O Footprint: Authentic external network, database, or graph drivers.
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set


# Patterns forbidden by Rule §4 and production ground-truth standards
SYNTHETIC_PATTERNS = [
    (r"\b(thomas|theo)\s+vance\b", "Fictional Vance fiduciary name"),
    (r"\b555-\d{4}\b", "Fake phone number (555 exchange)"),
    (r"\b(fake|dummy|mock|sample)_data\b", "Explicit synthetic/mock data identifier"),
    (r"\bhash\(.+\)\s*%\s*\d+", "Deterministic modulo hash used for synthetic score/math"),
    (r"\brandom\.(choice|randint|uniform)\b", "Random synthetic generator in business logic"),
    (r"\bJPMorgan\s+Chase\b.*\b(deed|mortgage)\b", "Synthetic deed/mortgage placeholder"),
    (r"\bstatus\s*=\s*['\"]SUCCESS['\"].*200", "Hardcoded fake success without network call"),
]

# External authentic I/O signatures
AUTHENTIC_IO_MODULES = {
    "httpx", "requests", "aiohttp", "urllib3", "sqlalchemy",
    "asyncpg", "psycopg2", "neo4j", "redis", "aioredis", "boto3"
}


class ModuleVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.classes: List[str] = []
        self.functions: List[str] = []
        self.not_implemented_nodes: List[int] = []
        self.pass_only_functions: List[str] = []
        self.bare_excepts: List[int] = []
        self.swallowed_exceptions: List[int] = []
        self.imports: Set[str] = set()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.append(node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.functions.append(node.name)
        # Check if function body is just 'pass' or docstring + 'pass'
        body = [n for n in node.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
        if len(body) == 1 and isinstance(body[0], ast.Pass):
            self.pass_only_functions.append(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.functions.append(node.name)
        body = [n for n in node.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
        if len(body) == 1 and isinstance(body[0], ast.Pass):
            self.pass_only_functions.append(node.name)
        self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise) -> None:
        if node.exc and isinstance(node.exc, ast.Call) and getattr(node.exc.func, "id", None) == "NotImplementedError":
            self.not_implemented_nodes.append(node.lineno)
        elif node.exc and getattr(node.exc, "id", None) == "NotImplementedError":
            self.not_implemented_nodes.append(node.lineno)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None:
            self.bare_excepts.append(node.lineno)
        # Check for pass/swallowed in except
        body = [n for n in node.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
        if len(body) == 1 and isinstance(body[0], ast.Pass):
            self.swallowed_exceptions.append(node.lineno)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.add(alias.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imports.add(node.module.split(".")[0])
        self.generic_visit(node)


def find_inbound_references(root_dir: Path, module_path: Path, visitor: ModuleVisitor) -> List[str]:
    """Find all files that import the target module or its exported symbols."""
    rel_stem = module_path.stem
    callers = []
    
    patterns = [
        re.compile(rf"\bfrom\s+[\.\w]*\b{re.escape(rel_stem)}\b"),
        re.compile(rf"\bimport\s+[\.\w]*\b{re.escape(rel_stem)}\b"),
    ]
    if visitor.classes:
        class_group = "|".join(re.escape(c) for c in visitor.classes)
        patterns.append(re.compile(rf"\b({class_group})\b"))
    
    for py_file in root_dir.rglob("*.py"):
        if py_file.resolve() == module_path.resolve():
            continue
        if ".venv" in py_file.parts or "site-packages" in py_file.parts or ".git" in py_file.parts:
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            if any(p.search(content) for p in patterns):
                callers.append(str(py_file.relative_to(root_dir)))
        except Exception:
            continue
    return callers


def audit_single_file(file_path: Path, root_dir: Path) -> Dict[str, Any]:
    rel_path = file_path.relative_to(root_dir) if file_path.is_relative_to(root_dir) else file_path
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    # 1. AST Parsing
    visitor = ModuleVisitor()
    parse_error = None
    try:
        tree = ast.parse(content, filename=str(file_path))
        visitor.visit(tree)
    except SyntaxError as e:
        parse_error = str(e)

    # 2. Synthetic Pattern Scan
    synthetic_matches = []
    for lineno, line in enumerate(lines, 1):
        for pattern, label in SYNTHETIC_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                synthetic_matches.append({
                    "line": lineno,
                    "text": line.strip(),
                    "issue": label
                })

    # 3. I/O Analysis
    io_drivers = visitor.imports.intersection(AUTHENTIC_IO_MODULES)

    # 4. Inbound Import References
    callers = find_inbound_references(root_dir, file_path, visitor)

    # 5. Scoring Calculation
    # Completeness
    completeness_deductions = (
        len(visitor.not_implemented_nodes) * 15 +
        len(visitor.pass_only_functions) * 10 +
        len(visitor.bare_excepts) * 10 +
        len(visitor.swallowed_exceptions) * 5 +
        (50 if parse_error else 0)
    )
    completeness_score = max(0, 100 - completeness_deductions)

    # Usefulness / Wiring
    usefulness_score = 100 if len(callers) >= 2 else (60 if len(callers) == 1 else 30)
    if "api" in str(file_path) or "main" in str(file_path):
        usefulness_score = 100  # Entrypoints have no incoming internal imports

    # Authenticity
    authenticity_deductions = len(synthetic_matches) * 25
    authenticity_score = max(0, 100 - authenticity_deductions)

    # Verdict
    if authenticity_score < 70:
        verdict = "MAKE_REAL"
    elif usefulness_score < 40:
        verdict = "DEPRECATE_AND_PURGE"
    elif completeness_score < 75:
        verdict = "KEEP_AND_HARDEN"
    else:
        verdict = "KEEP_AND_HARDEN"

    return {
        "file": str(rel_path),
        "classes": visitor.classes,
        "functions": visitor.functions,
        "not_implemented": visitor.not_implemented_nodes,
        "pass_only_functions": visitor.pass_only_functions,
        "bare_excepts": visitor.bare_excepts,
        "swallowed_exceptions": visitor.swallowed_exceptions,
        "synthetic_violations": synthetic_matches,
        "io_drivers": list(io_drivers),
        "callers": callers,
        "scores": {
            "completeness": completeness_score,
            "usefulness": usefulness_score,
            "authenticity": authenticity_score,
            "overall": round((completeness_score * 0.35 + usefulness_score * 0.25 + authenticity_score * 0.40)),
        },
        "verdict": verdict,
        "parse_error": parse_error,
    }


def print_report(res: Dict[str, Any]) -> None:
    print("\n" + "=" * 78)
    print(f"MODULE FORENSIC AUDIT: {res['file']}")
    print("=" * 78)
    scores = res["scores"]
    print(f"VERDICT:   [{res['verdict']}]")
    print(f"OVERALL GRADE: {scores['overall']}% | Completeness: {scores['completeness']}% | Usefulness: {scores['usefulness']}% | Authenticity: {scores['authenticity']}%")
    print("-" * 78)

    print(f"* Active Inbound Callers ({len(res['callers'])}):")
    if res["callers"]:
        for caller in res["callers"][:5]:
            print(f"    - {caller}")
        if len(res["callers"]) > 5:
            print(f"    ... and {len(res['callers']) - 5} more")
    else:
        print("    [!] WARNING: No inbound callers found (potential orphaned/dead module)")

    print(f"* Authentic I/O Drivers Detected: {', '.join(res['io_drivers']) if res['io_drivers'] else 'None (In-Memory / Pure Logic)'}")

    if res["synthetic_violations"]:
        print(f"\n[!] SYNTHETIC / MOCK VIOLATIONS DETECTED ({len(res['synthetic_violations'])}):")
        for v in res["synthetic_violations"]:
            print(f"    Line {v['line']}: {v['issue']}")
            print(f"      Code: {v['text']}")
    else:
        print("\n[OK] Authenticity Check: Zero synthetic entities / mock patterns detected.")

    if res["not_implemented"] or res["pass_only_functions"] or res["bare_excepts"]:
        print("\n[!] COMPLETENESS & EDGE CASE ISSUES:")
        for line in res["not_implemented"]:
            print(f"    Line {line}: raise NotImplementedError")
        for fn in res["pass_only_functions"]:
            print(f"    Function '{fn}': Stub body (pass only)")
        for line in res["bare_excepts"]:
            print(f"    Line {line}: Bare except: clause (swallows all exceptions)")
    else:
        print("[OK] Completeness Check: No stubs, NotImplementedErrors, or bare except clauses.")

    print("=" * 78 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit module for completeness, usefulness, authenticity, and realization.")
    parser.add_argument("target", help="Path to Python file or directory to audit")
    parser.add_argument("--root", default=".", help="Root directory of workspace (default: current dir)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()
    target_path = Path(args.target).resolve()
    root_dir = Path(args.root).resolve()

    if not target_path.exists():
        print(f"Error: Target path '{target_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    files_to_audit: List[Path] = []
    if target_path.is_file() and target_path.suffix == ".py":
        files_to_audit.append(target_path)
    elif target_path.is_dir():
        files_to_audit.extend([p for p in target_path.rglob("*.py") if "__pycache__" not in str(p) and "tests" not in str(p)])

    results = []
    for file_path in files_to_audit:
        res = audit_single_file(file_path, root_dir)
        results.append(res)
        if not args.json:
            print_report(res)

    if args.json:
        import json
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
