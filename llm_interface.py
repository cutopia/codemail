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
        
    def _make_request(self, messages: List[Dict[str, str]], max_tokens: int = None) -> Optional[str]:
        """
        Make a request to the LM Studio API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens in response (uses config default if None)
            
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
            
            # Use config default if not specified
            token_limit = max_tokens if max_tokens is not None else llm_config.max_tokens
            
            data = {
                "messages": messages,
                "max_tokens": token_limit,
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
            List of extracted bash command strings (only valid bash commands)
        """
        import re
        
        # Pattern to match ```bash ... ``` or ``` ... ``` blocks
        pattern = r'```(?:bash)?\s*([\s\S]*?)```'
        matches = re.findall(pattern, text)
        
        commands = []
        for match in matches:
            # Split the match into individual commands (separated by newlines)
            lines = [line.strip() for line in match.split('\n') if line.strip()]
            
            i = 0
            while i < len(lines):
                cmd = lines[i]
                
                # CRITICAL FIX: For heredoc commands (cat > file << EOF), extract only the command line
                # not the entire heredoc content. This prevents filtering out valid commands.
                
                # Check if this is a heredoc command and extract just the command part
                heredoc_match = re.match(r'^(cat|echo)\s+>[^\n]*', cmd)
                if heredoc_match:
                    cmd = heredoc_match.group(0).strip()
                
                # Skip if empty
                if not cmd:
                    i += 1
                    continue
                
                # CRITICAL FIX: Validate that this is actually a bash command, not natural language
            # Natural language responses often contain phrases like "I don't have", "Please clarify",
            # "To accomplish this", etc. We should filter these out.
            
            # Check for common natural language patterns that indicate non-command text
            natural_language_indicators = [
                r'^I\s+(don\'t|do\s+not)\s+hav',
                r'^Please\s+clarif',
                r'^To\s+accomplish',
                r'^Once\s+clarifi',
                r'^You\s+are\s+a',
                r'^CRITICAL\s+REQUIREMENTS',
                r'^Bash\s+Command',
                r'^Required\s+Response',
                r'^##\s+Summary',
                r'^##\s+Steps',
                r'^##\s+Results',
                r'^##\s+Errors',
                # NEW: Filter out project names, markdown syntax, and other non-command text
                r'^markdown$',
                r'^Bliss\s*\(',
                r'^[A-Z][a-z]+\s+\(\d{4}\)$',  # Project name with year like "Project (2026)"
                r'^[A-Za-z_]+\s+[A-Z]',         # Two words where second starts with capital
            ]
            
            is_natural_language = False
            for indicator in natural_language_indicators:
                if re.match(indicator, cmd, re.IGNORECASE | re.MULTILINE):
                    is_natural_language = True
                    break
            
            # CRITICAL FIX: Handle heredoc commands specially - they contain natural language but are valid bash
            is_heredoc_command = False
            if '<<' in cmd and ('cat >' in cmd or 'echo >' in cmd):
                is_heredoc_command = True
            
            # Also check for common LLM response patterns that aren't commands
            if not is_natural_language and not is_heredoc_command:
                # Check if the text contains mostly natural language (has many spaces between words)
                # vs. being a concise command
                word_count = len(cmd.split())
                
                # If it's very long and has natural language structure, skip it
                # BUT allow heredoc commands which naturally have more content
                if not is_heredoc_command and word_count > 20 and any(phrase in cmd.lower() for phrase in [
                    'i don\'t have',
                    'please clarify',
                    'to accomplish this',
                    'once clarified',
                    'you are a coding assistant'
                ]):
                    is_natural_language = True
            
            # NEW: Additional filtering for non-command text that might slip through
            if not is_natural_language and not is_heredoc_command:
                # Check for common patterns that indicate non-bash content
                cmd_lower = cmd.lower()
                
                # Skip if it's just a single word that doesn't look like a command
                if word_count == 1 and not any(cmd_lower.startswith(prefix) for prefix in [
                    'ls', 'cd', 'cat', 'echo', 'mkdir', 'rm', 'cp', 'mv', 
                    'git', 'python', 'node', 'npm', 'curl', 'wget', 'chmod'
                ]):
                    is_natural_language = True
                
                # Skip if it contains markdown-style formatting
                if re.search(r'^#{1,6}\s+', cmd) or re.search(r'\*\*.*\*\*', cmd):
                    is_natural_language = True
                
                # Skip if it looks like a heading or title (all caps with spaces)
                if word_count <= 3 and cmd.isupper() and ' ' in cmd:
                    is_natural_language = True
            
            # Only add if it's not natural language (or is a heredoc command)
            if not is_natural_language or is_heredoc_command:
                commands.append(cmd)
        
        return commands
    
    def _extract_bash_commands_v2(self, text: str) -> List[str]:
        """
        Extract bash commands from markdown code blocks (improved version).
        
        This version extracts individual commands from heredoc blocks.
        
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
            lines = match.strip().split('\n')
            
            # Process each line
            for line in lines:
                line = line.strip()
                
                # Skip empty lines and EOF markers
                if not line or line == 'EOF':
                    continue
                
                # Skip heredoc start markers like cat > file << 'EOF'
                if re.match(r'^(cat|echo)\s+>[^\n]*<<\s*[\'"]?EOF[\'"]?', line):
                    # Extract just the command part before the heredoc
                    cmd_part = re.split(r'\s*<<\s*', line)[0].strip()
                    if cmd_part and not any(ind in cmd_part.lower() for ind in ['i don\'t', 'please clarify']):
                        commands.append(cmd_part)
                    continue
                
                # Skip lines that are part of heredoc content (not actual commands)
                # Skip comment lines, variable assignments, and markdown-style list items
                if re.match(r'^[A-Za-z_]+\s+=\s+', line) or re.match(r'^#', line):
                    continue
                
                # Check for natural language patterns
                natural_language_indicators = [
                    r'^I\s+(don\'t|do\s+not)\s+hav',
                    r'^Please\s+clarif',
                    r'^To\s+accomplish',
                    r'^Once\s+clarifi',
                    r'^You\s+a\s+a',
                    r'^CRITICAL\s+REQUIREMENTS',
                ]
                
                is_natural_language = False
                for indicator in natural_language_indicators:
                    if re.match(indicator, line, re.IGNORECASE):
                        is_natural_language = True
                        break
                
                # Skip lines that look like heredoc content (not commands)
                # These are typically indented or start with special characters
                if re.match(r'^\s', line) and not re.match(r'^[a-zA-Z]', line):
                    continue
                
                # Skip markdown-style list items
                if re.match(r'^[-*]\s+', line):
                    continue
                
                # NEW: Additional filtering for non-command text
                # Check for project names, markdown syntax, and other non-bash content
                additional_indicators = [
                    r'^markdown$',
                    r'^Bliss\s*\(',
                    r'^[A-Z][a-z]+\s+\(\d{4}\)$',  # Project name with year like "Project (2026)"
                    r'^#{1,6}\s+',                  # Markdown headings
                    r'\*\*.*\*\*',                 # Bold markdown text
                ]
                
                is_additional_natural_language = False
                for indicator in additional_indicators:
                    if re.match(indicator, line, re.IGNORECASE):
                        is_additional_natural_language = True
                        break
                
                # Skip single words that don't look like commands
                word_count = len(line.split())
                if word_count == 1 and not any(line.lower().startswith(prefix) for prefix in [
                    'ls', 'cd', 'cat', 'echo', 'mkdir', 'rm', 'cp', 'mv', 
                    'git', 'python', 'node', 'npm', 'curl', 'wget', 'chmod'
                ]):
                    is_additional_natural_language = True
                
                # Only add if it's not natural language and looks like a command
                if not is_natural_language and not is_additional_natural_language and len(line.split()) <= 15:
                    commands.append(line)
        
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
1. ALL tasks MUST be accomplished using bash commands wrapped in ```bash code blocks
2. NEVER write files directly - always use bash commands like echo, cat, mkdir, cp, mv, rm, etc.
3. After any file operation, verify it exists with ls or cat
4. For listing files, ALWAYS use 'ls -la' command
5. ALL commands execute in the project workspace directory

Bash Command Execution:
- ALL actions must be wrapped in ```bash code blocks
- Commands execute in: {project_context}
- Always verify file creation/modification with ls -la after operations
- Example for listing files: 
  ```bash
  ls -la /path/to/workspace
  ```
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

Example of correct response format for listing files:
```bash
ls -la /path/to/workspace
```

Example of correct response format for creating/modifying files:
```bash
ls -la /path/to/workspace
cat > AGENTS.md << 'EOF'
# Project Documentation
Content here...
EOF
ls -la AGENTS.md
cat AGENTS.md
```

IMPORTANT: If the task involves creating or modifying files, you MUST include bash commands to create those files. Do not just describe what you would do - actually execute the commands.

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
            user_prompt += "CRITICAL: ALL tasks MUST be accomplished using bash commands in this directory.\n"
            user_prompt += "For listing files, use 'ls -la'.\n"
            user_prompt += "For creating/modifying files, use 'cat > filename' or similar bash commands.\n"
            user_prompt += "After any file operation, verify it exists with 'ls -la <filename>' and optionally show its contents with 'cat <filename>'.\n"
            user_prompt += "Wrap ALL bash commands in ```bash code blocks in your response."
            
            # CRITICAL: Add explicit file creation example based on instructions
            if any(keyword in instructions.lower() for keyword in ['create', 'generate', 'write', '.md', '.txt', '.py']):
                user_prompt += "\n\nEXAMPLE FILE CREATION COMMAND:\n"
                user_prompt += "If you need to create a file, use the following format:\n"
                user_prompt += "```bash\n"
                user_prompt += "cat > AGENTS.md << 'EOF'\n"
                user_prompt += "# Project Documentation\n"
                user_prompt += "Content goes here...\n"
                user_prompt += "EOF\n"
                user_prompt += "ls -la AGENTS.md\n"
                user_prompt += "cat AGENTS.md\n"
                user_prompt += "```\n"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Make LLM request with configurable max_tokens
        response = self._make_request(messages, max_tokens=llm_config.max_tokens)
        
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
        
        # CRITICAL FIX: Use the actual project context path directly when available
        # The workspace manager's execute_in_workspace uses its own base directory,
        # so we need to handle this differently. If project_context is an absolute path,
        # we should use it directly instead of converting to a project name.
        
        if bash_executor and bash_commands:
            for cmd in bash_commands:
                try:
                    # CRITICAL FIX: Validate command before execution
                    # Check if it's a natural language response that should be filtered out
                    import re
                    
                    # Use the same validation logic as workspace_manager
                    natural_language_indicators = [
                        r'^I\s+(don\'t|do\s+not)\s+hav',
                        r'^Please\s+clarif',
                        r'^To\s+accomplish',
                        r'^Once\s+clarifi',
                        r'^You\s+are\s+a',
                        r'^CRITICAL\s+REQUIREMENTS',
                        r'^Bash\s+Command',
                        r'^##\s+Summary',
                        r'^##\s+Steps',
                        r'^##\s+Results',
                        r'^##\s+Errors',
                    ]
                    
                    additional_indicators = [
                        r'^markdown$',
                        r'^Bliss\s*\(',
                        r'^[A-Z][a-z]+\s+\(\d{4}\)$',
                        r'^#{1,6}\s+',
                        r'\*\*.*\*\*',
                    ]
                    
                    is_natural_language = False
                    for indicator in natural_language_indicators + additional_indicators:
                        if re.match(indicator, cmd, re.IGNORECASE | re.MULTILINE):
                            is_natural_language = True
                            break
                    
                    # Also check single words that don't look like commands
                    word_count = len(cmd.split())
                    if word_count == 1 and not any(cmd.lower().startswith(prefix) for prefix in [
                        'ls', 'cd', 'cat', 'echo', 'mkdir', 'rm', 'cp', 'mv',
                        'git', 'python', 'node', 'npm', 'curl', 'wget', 'chmod',
                        'pwd', 'whoami', 'date', 'time', 'sleep', 'test', 'true', 'false'
                    ]):
                        is_natural_language = True
                    
                    if is_natural_language:
                        logger.warning(f"Command filtered out (natural language): {cmd[:50]}...")
                        bash_results.append({
                            "command": cmd,
                            "result": {
                                "stdout": "",
                                "stderr": f"Error: Natural language response detected and not executed: {cmd[:100]}...",
                                "returncode": -1
                            }
                        })
                        continue
                    
                    # Execute command in the appropriate directory
                    if project_context and os.path.isabs(project_context):
                        # Execute directly in absolute path directory
                        result = subprocess.run(
                            cmd,
                            shell=True,
                            cwd=project_context,
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                    else:
                        # Use the workspace manager with project name
                        result = bash_executor.execute_command(cmd, project_name=project_context or "default")
                    bash_results.append({
                        "command": cmd,
                        "result": result
                    })
                    
                    # Add command output to response for LLM to see
                    if result.get("returncode", 0) == 0:
                        response += f"\n\n[Bash Command Output]\nCommand: {cmd}\nOutput:\n{result.get('stdout', '')}"
                        
                        # CRITICAL FIX: Verify file was actually created
                        if 'cat >' in cmd or 'echo >' in cmd:
                            import re
                            match = re.search(r'(?:cat|echo)\s+>[^\n]*?["\']?([^"\'\n<>|;]+)["\']?', cmd)
                            if match:
                                filename = match.group(1).strip()
                                workspace_path = project_context or '.'
                                filepath = os.path.join(workspace_path, filename) if not os.path.isabs(filename) else filename
                                if os.path.exists(filepath):
                                    response += f"\n[File Created Successfully: {filename}]"
                                else:
                                    response += f"\n[WARNING: File {filename} may not have been created properly]"
                    else:
                        # Include comprehensive error information
                        stderr = result.get("stderr", "")
                        returncode = result.get("returncode", -1)
                        
                        error_info = f"Command: {cmd}\nExit Code: {returncode}\nError:\n{stderr}"
                        
                        if not stderr and returncode != 0:
                            # Try to provide more context for common failure modes
                            error_info += "\n\nNote: Command failed with non-zero exit code but no stderr output."
                            error_info += "\nPossible causes:"
                            error_info += "\n- File/directory permissions issue"
                            error_info += "\n- Path does not exist"
                            error_info += "\n- Invalid command syntax"
                        
                        response += f"\n\n[Bash Command Error]\n{error_info}"
                        
                except Exception as e:
                    # Include exception details in bash results
                    bash_results.append({
                        "command": cmd,
                        "result": {
                            "stdout": "",
                            "stderr": str(e),
                            "returncode": -1
                        }
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
            
            # Use configurable max_tokens for refinement iterations
            refined_response = self._make_request(messages, max_tokens=llm_config.max_tokens)
            
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
                    
                    # Get LLM's review of the bash execution with configurable max_tokens
                    llm_review = self._make_request(messages, max_tokens=llm_config.max_tokens)
                    
                    logger.debug(f"LLM review: {llm_review[:100] if llm_review else 'None'}...")
            
            # Use LLM review as basis for next iteration if available and task not complete
            if llm_review:
                # Check if LLM review indicates completion (just "TASK_COMPLETE" with no other content)
                review_upper = llm_review.upper()
                
                # CRITICAL FIX: Only mark complete if we actually have file creation commands that were executed
                has_file_commands = any(cmd.strip().startswith(('cat >', 'echo >', 'mkdir -p')) for cmd in bash_commands) if bash_commands else False
                
                if "TASK_COMPLETE" in review_upper and len(llm_review.strip()) < 50:
                    # CRITICAL FIX: If no bash commands were executed, don't mark complete
                    if not bash_commands:
                        logger.warning("LLM marked task complete but NO bash commands were executed")
                        logger.warning(f"LLM response: '{llm_review}'")
                        current_output = llm_review + "\n\nERROR: No bash commands were executed. Please execute bash commands to create files."
                        iteration_history.append(current_output)
                        continue  # Continue to next iteration to execute commands
                    
                    # Verify files were actually created before marking complete
                    if has_file_commands and project_path:
                        # Check if expected files exist
                        files_created = []
                        for cmd in bash_commands:
                            if 'cat >' in cmd or 'echo >' in cmd:
                                # Extract filename from command
                                import re
                                # Try heredoc pattern first, then simple redirection
                                match = re.search(r'(?:cat|echo)\s+>[^\n]*?["\']?([^"\'\n<>|;\s]+)["\']?', cmd)
                                if not match:
                                    # For echo "content" > file.txt format
                                    match = re.search(r'>(?:\s+|\s*"[^"]*"\s*)?([^"\'\n<>|;\s]+)', cmd)
                                if match:
                                    files_created.append(match.group(1).strip())
                        
                        if files_created:
                            missing_files = [f for f in files_created if not os.path.exists(os.path.join(project_path, f))]
                            if missing_files:
                                # CRITICAL FIX: Enhanced logging with workspace context
                                logger.warning(f"Task marked complete but files are missing: {missing_files}")
                                logger.warning(f"Project path: {project_path}")
                                logger.warning(f"Files in project directory: {os.listdir(project_path) if os.path.exists(project_path) else 'N/A'}")
                                
                                # Log each file's status
                                for f in files_created:
                                    filepath = os.path.join(project_path, f)
                                    exists = os.path.exists(filepath)
                                    size = os.path.getsize(filepath) if exists else 0
                                    logger.warning(f"File '{f}': exists={exists}, size={size} bytes")
                                
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
        # CRITICAL FIX: Validate that the command is actually a bash command, not natural language
        import re
        
        natural_language_indicators = [
            r'^I\s+(don\'t|do\s+not)\s+hav',
            r'^Please\s+clarif',
            r'^To\s+accomplish',
            r'^Once\s+clarifi',
            r'^You\s+are\s+a',
            r'^CRITICAL\s+REQUIREMENTS',
            r'^Bash\s+Command',
            r'^##\s+Summary',
            r'^##\s+Steps',
            r'^##\s+Results',
            r'^##\s+Errors',
        ]
        
        for indicator in natural_language_indicators:
            if re.match(indicator, command, re.IGNORECASE | re.MULTILINE):
                logger.warning(f"Skipping natural language response as bash command: {command[:50]}...")
                return {
                    "stdout": "",
                    "stderr": f"Error: Natural language response detected and not executed: {command[:100]}...",
                    "returncode": -1,
                    "command": command,
                    "timestamp": datetime.now().isoformat()
                }
        
        # Also check for common LLM response patterns
        if any(phrase in command.lower() for phrase in [
            'i don\'t have',
            'please clarify',
            'to accomplish this',
            'once clarified',
            'you are a coding assistant'
        ]):
            logger.warning(f"Skipping natural language response as bash command: {command[:50]}...")
            return {
                "stdout": "",
                "stderr": f"Error: Natural language response detected and not executed: {command[:100]}...",
                "returncode": -1,
                "command": command,
                "timestamp": datetime.now().isoformat()
            }
        
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
