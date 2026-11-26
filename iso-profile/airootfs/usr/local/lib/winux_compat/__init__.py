"""WINUX Windows compatibility layer: prefix, PE inspection, and runner orchestration."""

from .config import PrefixConfig, default_prefix_root, default_state_dir, sanitize_prefix_name
from .detector import BinaryInfo, classify_target, inspect_pe
from .prefixes import PrefixManager
from .runner import build_command, build_environment, launch_target
from .shortcuts import generate_shortcuts_for_prefix, scan_prefix_executables

__all__ = [
    "BinaryInfo",
    "PrefixConfig",
    "PrefixManager",
    "build_command",
    "build_environment",
    "classify_target",
    "default_prefix_root",
    "default_state_dir",
    "generate_shortcuts_for_prefix",
    "inspect_pe",
    "launch_target",
    "sanitize_prefix_name",
    "scan_prefix_executables",
]
