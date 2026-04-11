#!/usr/bin/env python3
"""
Diagnostic script for file creation issues in Codemail.
Analyzes task execution logs and workspace state to identify why files weren't created.
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.getcwd())

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("codemail.diagnose")


def analyze_task_result(task_file: str) -> dict:
    """
    Analyze a task result file to diagnose file creation issues.
    
    Args:
        task_file: Path to the task result JSON file
        
    Returns:
        Dictionary with diagnostic information
    """
    logger.info(f"Analyzing task result: {task_file}")
    
    try:
        with open(task_file, 'r') as f:
            result = json.load(f)
    except Exception as e:
        return {
            "error": f"Failed to load task file: {e}",
            "diagnosis": None
        }
    
    diagnostics = {
        "task_id": result.get("task_id", "unknown"),
        "status": result.get("status", "unknown"),
        "project_name": result.get("project_name", "default"),
        "workspace_path": result.get("workspace_path"),
        "instructions": result.get("instructions", "")[:200],
        "files_expected": [],
        "files_created": [],
        "missing_files": [],
        "bash_commands": [],
        "bash_results": [],
        "diagnosis": None
    }
    
    # Extract expected files from instructions
    instructions = result.get("instructions", "")
    potential_files = re.findall(r'([A-Za-z_]+\.(?:md|txt|py|json))', instructions)
    diagnostics["files_expected"] = list(set(potential_files))
    
    # Get bash commands and results
    if "bash_commands" in result:
        diagnostics["bash_commands"] = result["bash_commands"]
    
    if "bash_results" in result:
        diagnostics["bash_results"] = result["bash_results"]
        
        # Analyze bash command execution
        for i, cmd_result in enumerate(diagnostics["bash_results"]):
            cmd = cmd_result.get("command", "")
            res = cmd_result.get("result", {})
            
            # Check if file creation commands were executed
            if 'cat >' in cmd or 'echo >' in cmd:
                # Extract filename from command
                match = re.search(r'(?:cat|echo)\s+>[^\n]*?["\']?([^"\'\n<>|;\s]+)["\']?', cmd)
                if not match:
                    match = re.search(r'>(?:\s+|\s*"[^"]*"\s*)?([^"\'\n<>|;\s]+)', cmd)
                
                if match:
                    filename = match.group(1).strip()
                    
                    # Check if file was actually created
                    workspace_path = result.get("workspace_path", "./projects/default")
                    filepath = os.path.join(workspace_path, filename)
                    
                    diagnostics["bash_results"][i]["filename"] = filename
                    diagnostics["bash_results"][i]["filepath"] = filepath
                    diagnostics["bash_results"][i]["file_exists"] = os.path.exists(filepath)
                    
                    if not os.path.exists(filepath):
                        diagnostics["missing_files"].append(filename)
                        logger.warning(f"File expected but not created: {filename}")
    
    # Check workspace directory directly
    workspace_path = result.get("workspace_path", "./projects/default")
    if os.path.exists(workspace_path):
        actual_files = [f for f in os.listdir(workspace_path) 
                       if os.path.isfile(os.path.join(workspace_path, f))]
        diagnostics["files_created"] = actual_files
        
        # Compare expected vs actual
        for expected_file in diagnostics["files_expected"]:
            filepath = os.path.join(workspace_path, expected_file)
            if not os.path.exists(filepath):
                diagnostics["missing_files"].append(expected_file)
    
    # Generate diagnosis
    if result.get("status") == "completed" and diagnostics["missing_files"]:
        diagnostics["diagnosis"] = {
            "issue": "Task marked complete but files were not created",
            "expected_files": diagnostics["files_expected"],
            "missing_files": list(set(diagnostics["missing_files"])),
            "bash_commands_executed": len(diagnostics["bash_commands"]),
            "file_creation_attempts": sum(1 for r in diagnostics["bash_results"] 
                                        if 'cat >' in r.get("command", "") or 'echo >' in r.get("command", ""))
        }
        
        # Check for common issues
        issues = []
        
        # Check bash command execution results
        for cmd_result in diagnostics["bash_results"]:
            res = cmd_result.get("result", {})
            returncode = res.get("returncode", 0)
            
            if returncode != 0:
                issues.append({
                    "type": "command_failed",
                    "command": cmd_result.get("command", ""),
                    "returncode": returncode,
                    "stderr": res.get("stderr", "")
                })
        
        # Check for natural language detection
        for cmd_result in diagnostics["bash_results"]:
            stderr = cmd_result.get("result", {}).get("stderr", "")
            if "natural language" in stderr.lower():
                issues.append({
                    "type": "natural_language_detected",
                    "command": cmd_result.get("command", ""),
                    "message": stderr
                })
        
        # Check for workspace path issues
        if not os.path.exists(workspace_path):
            issues.append({
                "type": "workspace_missing",
                "path": workspace_path
            })
        
        diagnostics["diagnosis"]["issues"] = issues
    
    return diagnostics


def analyze_workspace_state(project_name: str, base_dir: str = "./projects") -> dict:
    """
    Analyze the current state of a project workspace.
    
    Args:
        project_name: Name of the project
        base_dir: Base directory for projects
        
    Returns:
        Dictionary with workspace analysis
    """
    workspace_path = os.path.join(base_dir, project_name)
    
    analysis = {
        "project_name": project_name,
        "workspace_path": workspace_path,
        "exists": os.path.exists(workspace_path),
        "files": [],
        "permissions": None,
        "disk_space": None
    }
    
    if os.path.exists(workspace_path):
        # List files
        try:
            for item in os.listdir(workspace_path):
                item_path = os.path.join(workspace_path, item)
                analysis["files"].append({
                    "name": item,
                    "type": "file" if os.path.isfile(item_path) else "directory",
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
                })
        except Exception as e:
            analysis["error"] = str(e)
        
        # Check permissions
        try:
            analysis["permissions"] = {
                "readable": os.access(workspace_path, os.R_OK),
                "writable": os.access(workspace_path, os.W_OK),
                "executable": os.access(workspace_path, os.X_OK)
            }
        except Exception as e:
            analysis["permissions_error"] = str(e)
        
        # Check disk space
        try:
            stat = os.statvfs(workspace_path)
            analysis["disk_space"] = {
                "total_bytes": stat.f_frsize * stat.f_blocks,
                "free_bytes": stat.f_frsize * stat.f_bavail
            }
        except Exception as e:
            analysis["disk_space_error"] = str(e)
    
    return analysis


def generate_diagnostic_report(task_file: str = None, project_name: str = None) -> str:
    """
    Generate a comprehensive diagnostic report.
    
    Args:
        task_file: Path to task result file (optional)
        project_name: Name of project to analyze (optional)
        
    Returns:
        Formatted diagnostic report
    """
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("CODEMAIL FILE CREATION DIAGNOSTIC REPORT")
    report_lines.append(f"Generated: {datetime.now().isoformat()}")
    report_lines.append("=" * 80)
    
    # Analyze task result if provided
    if task_file:
        report_lines.append("\n### TASK RESULT ANALYSIS ###\n")
        
        diagnostics = analyze_task_result(task_file)
        
        if diagnostics.get("error"):
            report_lines.append(f"Error: {diagnostics['error']}")
        else:
            report_lines.append(f"Task ID: {diagnostics['task_id']}")
            report_lines.append(f"Status: {diagnostics['status']}")
            report_lines.append(f"Project: {diagnostics['project_name']}")
            
            if diagnostics.get("workspace_path"):
                report_lines.append(f"Workspace Path: {diagnostics['workspace_path']}")
            
            report_lines.append(f"\nInstructions (truncated):")
            report_lines.append(f"{diagnostics['instructions']}...")
            
            report_lines.append(f"\nExpected Files: {diagnostics['files_expected']}")
            report_lines.append(f"Files Created: {diagnostics['files_created']}")
            report_lines.append(f"Missing Files: {diagnostics['missing_files']}")
            
            if diagnostics.get("bash_commands"):
                report_lines.append(f"\nBash Commands Executed: {len(diagnostics['bash_commands'])}")
                
                for i, cmd in enumerate(diagnostics["bash_commands"][:5], 1):  # Show first 5
                    report_lines.append(f"  {i}. {cmd[:100]}...")
            
            if diagnostics.get("bash_results"):
                report_lines.append(f"\nBash Command Results:")
                
                for i, result in enumerate(diagnostics["bash_results"][:5], 1):
                    cmd = result.get("command", "")
                    res = result.get("result", {})
                    returncode = res.get("returncode", -1)
                    
                    status = "✅" if returncode == 0 else "❌"
                    report_lines.append(f"  {i}. {status} {cmd[:80]}")
                    report_lines.append(f"     Return Code: {returncode}")
                    
                    stderr = res.get("stderr", "")
                    if stderr:
                        report_lines.append(f"     Stderr: {stderr[:200]}")
            
            if diagnostics.get("diagnosis"):
                report_lines.append("\n### DIAGNOSIS ###\n")
                
                diagnosis = diagnostics["diagnosis"]
                report_lines.append(f"Issue: {diagnosis['issue']}")
                
                if diagnosis.get("issues"):
                    report_lines.append("\nIdentified Issues:")
                    for j, issue in enumerate(diagnosis["issues"], 1):
                        report_lines.append(f"  {j}. [{issue['type'].upper()}]")
                        
                        if issue.get("command"):
                            report_lines.append(f"     Command: {issue['command'][:80]}")
                        
                        if issue.get("returncode") is not None:
                            report_lines.append(f"     Return Code: {issue['returncode']}")
                        
                        if issue.get("stderr"):
                            report_lines.append(f"     Error: {issue['stderr'][:200]}")
    
    # Analyze workspace state if project name provided
    if project_name:
        report_lines.append("\n### WORKSPACE STATE ANALYSIS ###\n")
        
        workspace_analysis = analyze_workspace_state(project_name)
        
        report_lines.append(f"Project: {workspace_analysis['project_name']}")
        report_lines.append(f"Path: {workspace_analysis['workspace_path']}")
        report_lines.append(f"Exists: {'✅' if workspace_analysis['exists'] else '❌'}")
        
        if workspace_analysis.get("files"):
            report_lines.append("\nFiles in Workspace:")
            for file_info in workspace_analysis["files"]:
                size = file_info.get("size", "N/A")
                report_lines.append(f"  - {file_info['name']} ({size} bytes)")
        
        if workspace_analysis.get("permissions"):
            perms = workspace_analysis["permissions"]
            report_lines.append("\nPermissions:")
            report_lines.append(f"  Readable: {'✅' if perms.get('readable') else '❌'}")
            report_lines.append(f"  Writable: {'✅' if perms.get('writable') else '❌'}")
            report_lines.append(f"  Executable: {'✅' if perms.get('executable') else '❌'}")
        
        if workspace_analysis.get("disk_space"):
            space = workspace_analysis["disk_space"]
            report_lines.append("\nDisk Space:")
            report_lines.append(f"  Total: {space['total_bytes'] / (1024*1024):.2f} MB")
            report_lines.append(f"  Free: {space['free_bytes'] / (1024*1024):.2f} MB")
    
    # Add recommendations
    report_lines.append("\n### RECOMMENDATIONS ###\n")
    
    if task_file:
        diagnostics = analyze_task_result(task_file)
        
        if diagnostics.get("diagnosis") and diagnostics["diagnosis"].get("issues"):
            issues = diagnostics["diagnosis"]["issues"]
            
            for issue in issues:
                if issue["type"] == "command_failed":
                    report_lines.append("1. COMMAND FAILURE DETECTED")
                    report_lines.append("   - Check the command syntax")
                    report_lines.append("   - Verify file paths are correct")
                    report_lines.append("   - Ensure workspace directory exists and is writable")
                
                elif issue["type"] == "natural_language_detected":
                    report_lines.append("2. NATURAL LANGUAGE DETECTED AS COMMAND")
                    report_lines.append("   - LLM may be generating text instead of bash commands")
                    report_lines.append("   - Review prompt engineering to enforce command format")
                    report_lines.append("   - Consider adding more explicit examples")
                
                elif issue["type"] == "workspace_missing":
                    report_lines.append("3. WORKSPACE DIRECTORY MISSING")
                    report_lines.append("   - Workspace directory was not created")
                    report_lines.append("   - Check workspace manager initialization")
    
    report_lines.append("\n" + "=" * 80)
    report_lines.append("END OF DIAGNOSTIC REPORT")
    report_lines.append("=" * 80)
    
    return "\n".join(report_lines)


def main():
    """Main entry point for diagnostic script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Diagnose file creation issues in Codemail")
    parser.add_argument("--task", "-t", help="Path to task result JSON file")
    parser.add_argument("--project", "-p", help="Project name to analyze workspace")
    parser.add_argument("--output", "-o", help="Output file for report (default: stdout)")
    
    args = parser.parse_args()
    
    if not args.task and not args.project:
        parser.print_help()
        sys.exit(1)
    
    report = generate_diagnostic_report(args.task, args.project)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Diagnostic report saved to: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
