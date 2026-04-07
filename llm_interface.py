"""
LLM interface module for Codemail system.
Connects to local LM Studio endpoint and executes coding tasks with bash command execution.
"""

import requests
import json
import logging
import subprocess
import os
import re
from datetime import datetime
from typing import List, Dict, Optional, Any
from config import llm_config

logger = logging.getLogger("codemail.llm_interface")


class LLMInterface:
    """Interface to local LM Studio LLM endpoint."""
    
    def __init__(self):
        self.endpoint = llm_config.endpoint
        self.api_key = llm_config.api_key
        
    def _make_request(self, messages: List[Dict[str, str]], max_tokens: int = 2048) -> Optional[str]:
        """
        Make a request to the LM Studio API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens in response
            
        Returns:
            LLM response text or None if error
        """
        try:
            # Ensure endpoint has correct path format
            endpoint = self.endpoint.rstrip('/')
            
            # LM Studio OpenAI-compatible endpoint
            url = f"{endpoint}/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract content from response
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            
            logger.error(f"Unexpected API response format: {result}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in LLM request: {e}")
            return None
    
    def _extract_bash_commands(self, text: str) -> List[str]:
        """
        Extract bash commands from markdown code blocks.
        
        Args:
            text: Text potentially containing ```bash code blocks
            
        Returns:
            List of extracted bash command strings
        """
        import re
        
        # Pattern to match ```bash ... ``` or ``` ... ``` blocks
        pattern = r'```(?:bash)?\s*([\s\S]*?)```'
        matches = re.findall(pattern, text)
        
        commands = []
        for match in matches:
            # Clean up the command (remove leading/trailing whitespace)
            cmd = match.strip()
            if cmd:
                commands.append(cmd)
        
        return commands
    
    def execute_task(self, instructions: str, project_context: Optional[str] = None,
                    bash_executor=None) -> Dict:
        """
        Execute a coding task using the LLM with optional bash command execution.
        
        Args:
            instructions: Task instructions from email
            project_context: Optional context about the project (workspace path)
            bash_executor: Optional BashExecutor instance for running commands
            
        Returns:
            Dictionary with execution results including status, output, and errors
        """
        logger.info(f"Executing task with instructions: {instructions[:100]}...")
        
        # Build system prompt for coding agent with bash execution capability
        system_prompt = """You are an expert coding assistant. Your task is to analyze the project context and execute the user's instructions.

CRITICAL REQUIREMENTS:
1. ALL file operations MUST be performed using bash commands wrapped in ```bash code blocks
2. NEVER write files directly - always use bash commands like echo, cat, or mkdir
3. After creating a file, verify it exists with ls or cat
4. If the task involves creating, modifying, or deleting files, you MUST use bash commands

Bash Command Execution:
- ALL file operations must be wrapped in ```bash code blocks
- Commands execute in: {project_context}
- Always verify file creation with ls -la after writing files
- Example for creating a file: 
  ```bash
  cat > AGENTS.md << 'EOF'
  # Project Documentation
  This is the content.
  EOF
  ```

Required Response Format:
1. First, analyze the task and plan your approach
2. Execute bash commands to accomplish the task
3. Verify results with ls/cat commands
4. Report back with a comprehensive summary

Example of correct response format:
```bash
ls -la /path/to/workspace
cat > AGENTS.md << 'EOF'
# Project Documentation
Content here...
EOF
ls -la AGENTS.md
```

## Summary
Brief overview of what was accomplished

## Steps Taken
List of steps you executed, including any bash commands run

## Results
Final results and any output generated (including file contents if requested)

## Errors (if any)
Any errors encountered during execution"""
        
        # Build user prompt with project context if available
        user_prompt = f"INSTRUCTIONS:\n{instructions}"
        
        if project_context:
            user_prompt += f"\n\nPROJECT CONTEXT:\nWorkspace directory: {project_context}\n"
            user_prompt += "CRITICAL: All file operations MUST be performed using bash commands in this directory.\n"
            user_prompt += "First, run 'ls -la' to see existing files, then create/modify files as needed.\n"
            user_prompt += "After creating any file, verify it exists with 'ls -la <filename>' and optionally show its contents with 'cat <filename>'."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Make LLM request
        response = self._make_request(messages)
        
        if not response:
            return {
                "status": "failed",
                "output": None,
                "error": "Failed to get response from LLM"
            }
        
        logger.info("Task execution completed successfully")
        
        # Extract and execute any bash commands from the response
        bash_commands = self._extract_bash_commands(response)
        bash_results = []
        
        if bash_executor and bash_commands:
            for cmd in bash_commands:
                try:
                    result = bash_executor.execute_command(cmd, project_name="default")
                    bash_results.append({
                        "command": cmd,
                        "result": result
                    })
                    
                    # Add command output to response for LLM to see
                    if result.get("returncode", 0) == 0:
                        response += f"\n\n[Bash Command Output]\nCommand: {cmd}\nOutput:\n{result.get('stdout', '')}"
                    else:
                        response += f"\n\n[Bash Command Error]\nCommand: {cmd}\nError:\n{result.get('stderr', '')}"
                        
                except Exception as e:
                    bash_results.append({
                        "command": cmd,
                        "error": str(e)
                    })
        
        return {
            "status": "completed",
            "output": response,
            "error": None,
            "bash_commands_executed": len(bash_commands),
            "bash_results": bash_results
        }
    
    def execute_iterative_task_with_progress(self, instructions: str, task_id: str = None,
                                           progress_callback=None, max_iterations: int = 5,
                                           project_name: str = "default",
                                           workspace_path: str = None,
                                           bash_executor=None) -> Dict:
        """
        Execute a task with iterative refinement and progress tracking.
        
        Args:
            instructions: Task instructions from email
            task_id: Optional task ID for progress tracking
            progress_callback: Callback function for progress updates (task_id, current_step, total_steps, message)
            max_iterations: Maximum number of refinement iterations
            project_name: Name of the project (for workspace isolation)
            workspace_path: Path to project workspace directory
            
        Returns:
            Dictionary with final results including iteration history and step summaries.
            Step summaries contain descriptions of each execution step taken by the agent.
        """
        logger.info(f"Starting iterative task execution for project '{project_name}' (max {max_iterations} iterations)")
        
        # Track steps for progress and capture summaries
        total_steps = 1 + max_iterations  # Initial execution + max refinement iterations
        current_step = 0
        step_summaries = []  # Collect summaries of each step
        
        # Report initial step
        if progress_callback and task_id:
            try:
                progress_callback(task_id, current_step, total_steps, "Starting execution...")
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
        
        # Initial execution with project context
        result = self.execute_task(instructions, project_context=workspace_path)
        
        if result["status"] == "failed":
            return {
                **result,
                "iterations": 0,
                "iteration_history": [],
                "step_summaries": []
            }
        
        # Capture initial step summary with bash command details
        bash_commands_executed = result.get("bash_commands_executed", 0)
        bash_results = result.get("bash_results", [])
        
        # Build detailed summary of what happened
        initial_summary_parts = [f"Initial execution completed. Generated response with {len(result.get('output', ''))} characters."]
        
        if bash_commands_executed > 0:
            initial_summary_parts.append(f"\n**Bash Commands Executed ({bash_commands_executed}):**")
            for i, cmd_result in enumerate(bash_results, 1):
                cmd = cmd_result.get("command", "")
                res = cmd_result.get("result", {})
                stdout = res.get("stdout", "").strip()[:200] if res else ""  # Truncate long output
                stderr = res.get("stderr", "").strip()[:200] if res else ""
                returncode = res.get("returncode", 0)
                
                cmd_summary = f"{i}. `{cmd}`"
                if returncode == 0:
                    cmd_summary += f" ✅ (output: {stdout})"
                else:
                    cmd_summary += f" ❌ (error: {stderr})"
                initial_summary_parts.append(cmd_summary)
        
        initial_summary = "\n".join(initial_summary_parts)
        step_summaries.append({
            "step": current_step,
            "description": "Initial task execution",
            "summary": initial_summary,
            "timestamp": datetime.now().isoformat() if 'datetime' in dir() else None
        })
        
        iteration_history = [result["output"]]
        current_output = result["output"]
        
        # Iterative refinement (simple implementation)
        for i in range(1, max_iterations + 1):  # Fixed: now runs max_iterations times
            current_step += 1
            logger.info(f"Refinement iteration {i}/{max_iterations}")
            
            # Report progress
            if progress_callback and task_id:
                try:
                    progress_callback(task_id, current_step, total_steps, f"Refinement iteration {i}/{max_iterations}")
                except Exception as e:
                    logger.warning(f"Progress callback failed: {e}")
            
            # Ask LLM to review and improve its previous output
            refine_prompt = f"""Please review your previous response and identify areas for improvement.
If the task is complete, respond with "TASK_COMPLETE".
Otherwise, provide an improved version of your response.

Previous response:
{current_output}

Bash commands were executed in the workspace. Please review their output and continue if needed.

Your improved response:"""
            
            messages = [
                {"role": "system", "content": "You are a coding assistant reviewing your previous work. Be critical and improve where possible."},
                {"role": "user", "content": refine_prompt}
            ]
            
            refined_response = self._make_request(messages)
            
            if not refined_response:
                break
            
            # Extract and execute any bash commands from the refined response
            bash_commands = self._extract_bash_commands(refined_response)
            bash_results = []
            llm_review = None
            
            if bash_executor and bash_commands:
                for cmd in bash_commands:
                    try:
                        result = bash_executor.execute_command(cmd, project_name=project_name)
                        bash_results.append({
                            "command": cmd,
                            "result": result
                        })
                        
                        # Add command output to response for LLM to see
                        if result.get("returncode", 0) == 0:
                            refined_response += f"\n\n[Bash Command Output]\nCommand: {cmd}\nOutput:\n{result.get('stdout', '')}"
                        else:
                            refined_response += f"\n\n[Bash Command Error]\nCommand: {cmd}\nError:\n{result.get('stderr', '')}"
                            
                    except Exception as e:
                        bash_results.append({
                            "command": cmd,
                            "error": str(e)
                        })
                
                # After executing bash commands, ask LLM to review the output and continue
                logger.debug(f"Executing {len(bash_commands)} bash command(s)")
                
                if bash_commands:
                    review_prompt = f"""I executed the following bash command(s) in the project workspace:

{chr(10).join(f"- {cmd}" for cmd in bash_commands)}

The output was:

{chr(10).join(f"- Command: {r['command']}, Result: {str(r.get('result', {}))}" for r in bash_results)}

Please review this output and continue with the task if needed. If the task is complete, respond with "TASK_COMPLETE". Otherwise, provide your next step or improved response."""
                    
                    messages = [
                        {"role": "system", "content": "You are a coding assistant that executes bash commands and reviews their output."},
                        {"role": "user", "content": review_prompt}
                    ]
                    
                    # Get LLM's review of the bash execution
                    llm_review = self._make_request(messages, max_tokens=1024)
                    
                    logger.debug(f"LLM review: {llm_review[:100] if llm_review else 'None'}...")
            
            # Use LLM review as basis for next iteration if available and task not complete
            if llm_review:
                # Check if LLM review indicates completion (just "TASK_COMPLETE" with no other content)
                review_upper = llm_review.upper()
                
                # CRITICAL FIX: Only mark complete if we actually have file creation commands that were executed
                has_file_commands = any(cmd.strip().startswith(('cat >', 'echo >', 'mkdir -p')) for cmd in bash_commands) if bash_commands else False
                
                if "TASK_COMPLETE" in review_upper and len(llm_review.strip()) < 50:
                    # Verify files were actually created before marking complete
                    if has_file_commands and project_path:
                        # Check if expected files exist
                        files_created = []
                        for cmd in bash_commands:
                            if 'cat >' in cmd or 'echo >' in cmd:
                                # Extract filename from command
                                import re
                                match = re.search(r'(?:cat|echo)\s+>[^\n]*?["\']?([^"\'\n]+)["\']?', cmd)
                                if match:
                                    files_created.append(match.group(1).strip())
                        
                        if files_created:
                            missing_files = [f for f in files_created if not os.path.exists(os.path.join(project_path, f))]
                            if missing_files:
                                logger.warning(f"Task marked complete but files are missing: {missing_files}")
                                # Don't mark complete - continue iterations
                                current_output = llm_review + "\n\nWARNING: The following files were not created: " + ", ".join(missing_files)
                                iteration_history.append(current_output)
                                continue  # Continue to next iteration to create missing files
                    
                    logger.info("Task marked as complete by LLM after bash execution")
                    
                    current_output = refined_response
                    iteration_history.append(refined_response)
                    
                    # Capture final step summary with bash command details
                    final_summary_parts = [f"Task marked complete after {i} refinement iterations."]
                    
                    if bash_commands:
                        final_summary_parts.append(f"\n**Final Bash Commands Executed ({len(bash_commands)}):**")
                        for j, cmd_result in enumerate(bash_results, 1):
                            cmd = cmd_result.get("command", "")
                            res = cmd_result.get("result", {})
                            stdout = res.get("stdout", "").strip()[:200] if res else ""  # Truncate long output
                            stderr = res.get("stderr", "").strip()[:200] if res else ""
                            returncode = res.get("returncode", 0)
                            
                            cmd_summary = f"{j}. `{cmd}`"
                            if returncode == 0:
                                cmd_summary += f" ✅ (output: {stdout})"
                            else:
                                cmd_summary += f" ❌ (error: {stderr})"
                            final_summary_parts.append(cmd_summary)
                    
                    final_output_chars = len(current_output)
                    final_summary_parts.append(f"\n**Final Output:** {final_output_chars} characters")
                    
                    final_summary = "\n".join(final_summary_parts)
                    step_summaries.append({
                        "step": current_step,
                        "description": "Task completion review",
                        "summary": final_summary,
                        "timestamp": datetime.now().isoformat() if 'datetime' in dir() else None
                    })
                    
                    break  # Exit loop when task is complete
                else:
                    # LLM wants to continue - use the review as basis for next iteration
                    current_output = llm_review
            else:
                # No bash commands or no LLM review - use refined response
                current_output = refined_response
            
            iteration_history.append(current_output)
            
            # Capture refinement step summary with bash command details
            refinement_summary_parts = [f"Refinement iteration {i} completed."]
            
            if bash_commands:
                refinement_summary_parts.append(f"\n**Bash Commands Executed ({len(bash_commands)}):**")
                for j, cmd_result in enumerate(bash_results, 1):
                    cmd = cmd_result.get("command", "")
                    res = cmd_result.get("result", {})
                    stdout = res.get("stdout", "").strip()[:200] if res else ""  # Truncate long output
                    stderr = res.get("stderr", "").strip()[:200] if res else ""
                    returncode = res.get("returncode", 0)
                    
                    cmd_summary = f"{j}. `{cmd}`"
                    if returncode == 0:
                        cmd_summary += f" ✅ (output: {stdout})"
                    else:
                        cmd_summary += f" ❌ (error: {stderr})"
                    refinement_summary_parts.append(cmd_summary)
            
            # Add LLM review if available
            if llm_review:
                review_preview = llm_review.strip()[:300]
                refinement_summary_parts.append(f"\n**LLM Review:**\n{review_preview}")
            
            refinement_summary = "\n".join(refinement_summary_parts)
            step_summaries.append({
                "step": current_step,
                "description": f"Refinement iteration {i}",
                "summary": refinement_summary,
                "timestamp": datetime.now().isoformat() if 'datetime' in dir() else None
            })
        
        # Report final progress
        current_step += 1
        if progress_callback and task_id:
            try:
                progress_callback(task_id, current_step, total_steps, "Task completed")
            except Exception as e:
                logger.warning(f"Final progress callback failed: {e}")
        
        return {
            "status": "completed",
            "output": current_output,
            "error": None,
            "iterations": len(iteration_history),
            "iteration_history": iteration_history,
            "step_summaries": step_summaries
        }
    
    def execute_iterative_task(self, instructions: str, max_iterations: int = 5) -> Dict:
        """
        Execute a task with iterative refinement (legacy method).
        
        Args:
            instructions: Task instructions from email
            max_iterations: Maximum number of refinement iterations
            
        Returns:
            Dictionary with final results and iteration history
        """
        return self.execute_iterative_task_with_progress(instructions, max_iterations=max_iterations)
    
    def check_connection(self) -> bool:
        """Check if LLM endpoint is reachable."""
        try:
            # Simple test request
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello"}
            ]
            
            response = self._make_request(messages, max_tokens=10)
            
            return response is not None and len(response) > 0
            
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            return False


class BashExecutor:
    """Executes bash commands with project workspace isolation."""
    
    def __init__(self, base_workspace_dir: str = None):
        """
        Initialize bash executor.
        
        Args:
            base_workspace_dir: Base directory for project workspaces. Defaults to ./projects
        """
        try:
            from workspace_manager import WorkspaceManager
            self.workspace_manager = WorkspaceManager(base_workspace_dir)
        except ImportError:
            logger.warning("workspace_manager not available, using fallback")
            self.workspace_manager = None
    
    def execute_command(self, command: str, project_name: str = "default") -> Dict[str, Any]:
        """
        Execute a bash command in the appropriate workspace.
        
        Args:
            command: Bash command to execute
            project_name: Name of the project (for workspace isolation)
            
        Returns:
            Dictionary with execution results
        """
        if self.workspace_manager:
            return self.workspace_manager.execute_in_workspace(project_name, command)
        else:
            # Fallback: execute in current directory
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                    "command": command,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                return {
                    "stdout": "",
                    "stderr": str(e),
                    "returncode": -1,
                    "command": command,
                    "timestamp": datetime.now().isoformat()
                }


def create_llm_interface():
    """Factory function to create LLM interface."""
    llm = LLMInterface()
    
    # Test connection on creation
    if not llm.check_connection():
        logger.warning("LLM endpoint connection test failed. Tasks may fail.")
    
    return llm


def create_bash_executor(workspace_dir: str = None):
    """Factory function to create bash executor."""
    return BashExecutor(workspace_dir)
