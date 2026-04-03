"""
LLM interface module for Codemail system.
Connects to local LM Studio endpoint and executes coding tasks.
"""

import requests
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
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
    
    def execute_task(self, instructions: str, project_context: Optional[str] = None) -> Dict:
        """
        Execute a coding task using the LLM.
        
        Args:
            instructions: Task instructions from email
            project_context: Optional context about the project
            
        Returns:
            Dictionary with execution results including status, output, and errors
        """
        logger.info(f"Executing task with instructions: {instructions[:100]}...")
        
        # Build system prompt for coding agent
        system_prompt = """You are an expert coding assistant. Your task is to analyze the project context and execute the user's instructions.

Follow these guidelines:
1. First, understand the project structure and requirements
2. Break down complex tasks into smaller steps
3. Execute each step carefully
4. Report back with a comprehensive summary of what you did

Format your response as:
## Summary
Brief overview of what was accomplished

## Steps Taken
List of steps you executed

## Results
Final results and any output generated

## Errors (if any)
Any errors encountered during execution"""
        
        # Build user prompt with project context if available
        user_prompt = f"INSTRUCTIONS:\n{instructions}"
        
        if project_context:
            user_prompt += f"\n\nPROJECT CONTEXT:\n{project_context}"
        
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
        
        return {
            "status": "completed",
            "output": response,
            "error": None
        }
    
    def execute_iterative_task_with_progress(self, instructions: str, task_id: str = None,
                                           progress_callback=None, max_iterations: int = 5) -> Dict:
        """
        Execute a task with iterative refinement and progress tracking.
        
        Args:
            instructions: Task instructions from email
            task_id: Optional task ID for progress tracking
            progress_callback: Callback function for progress updates (task_id, current_step, total_steps, message)
            max_iterations: Maximum number of refinement iterations
            
        Returns:
            Dictionary with final results including iteration history and step summaries.
            Step summaries contain descriptions of each execution step taken by the agent.
        """
        logger.info(f"Starting iterative task execution (max {max_iterations} iterations)")
        
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
        
        # Initial execution
        result = self.execute_task(instructions)
        
        if result["status"] == "failed":
            return {
                **result,
                "iterations": 0,
                "iteration_history": [],
                "step_summaries": []
            }
        
        # Capture initial step summary
        initial_summary = f"Initial execution completed. Generated response with {len(result.get('output', ''))} characters."
        step_summaries.append({
            "step": current_step,
            "description": "Initial task execution",
            "summary": initial_summary,
            "timestamp": datetime.now().isoformat() if 'datetime' in dir() else None
        })
        
        iteration_history = [result["output"]]
        current_output = result["output"]
        
        # Iterative refinement (simple implementation)
        for i in range(1, max_iterations):
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

Your improved response:"""
            
            messages = [
                {"role": "system", "content": "You are a coding assistant reviewing your previous work. Be critical and improve where possible."},
                {"role": "user", "content": refine_prompt}
            ]
            
            refined_response = self._make_request(messages)
            
            if not refined_response:
                break
            
            # Check if task is complete
            if "TASK_COMPLETE" in refined_response.upper():
                logger.info("Task marked as complete by LLM")
                
                # Capture final step summary
                final_summary = f"Task marked complete after {i} refinement iterations. Final output has {len(refined_response)} characters."
                step_summaries.append({
                    "step": current_step,
                    "description": "Task completion review",
                    "summary": final_summary,
                    "timestamp": datetime.now().isoformat() if 'datetime' in dir() else None
                })
                
                current_step += 1  # Count this step
                break
            
            current_output = refined_response
            iteration_history.append(refined_response)
            
            # Capture refinement step summary
            refinement_summary = f"Refinement iteration {i} completed. Output improved with {len(refined_response)} characters."
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


def create_llm_interface():
    """Factory function to create LLM interface."""
    llm = LLMInterface()
    
    # Test connection on creation
    if not llm.check_connection():
        logger.warning("LLM endpoint connection test failed. Tasks may fail.")
    
    return llm
