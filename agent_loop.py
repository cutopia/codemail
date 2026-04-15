
import os
import subprocess
import time
import uuid
from config import settings
from llm_client import LLMClient
from email_handler import EmailHandler

class AgentLoop:
    def __init__(self):
        self.llm = LLMClient()
        self.email_handler = EmailHandler()

    def execute_bash(self, command, cwd=None):
        """
        Executes a bash command with a timeout to prevent hanging.
        """
        print(f"Executing: {command}")
        try:
            # Use subprocess.run with timeout for recovery from hanging calls
            result = subprocess.run(
                [ "bash", "-c", command ],
                capture_output=True,
                text=True,
                timeout=300, # 5 minutes timeout
                cwd=cwd or os.getcwd()
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired as e:
            return {
                "stdout": e.stdout.decode() if e.stdout else "",
                "stderr": f"Error: Command timed out after 300 seconds.\n{e.stderr.decode() if e.stderr else ''}",
                "exit_code": -1
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1
            }

    def run_task(self, task):
        """
        Main loop for a single task.
        """
        project_name = task['project']
        instructions = task['instructions']
        sender = task['sender']

        project_path = os.path.expanduser(settings.PROJECTS_BASE_DIR)
        if not os.path.exists(project_path):
            os.makedirs(project_path, exist_ok=True)
        
        full_project_dir = os.path.join(project_path, project_name)
        os.makedirs(full_project_dir, exist_ok=True)
        
        cwd = full_project_dir

        history = [] # Local history per task to avoid leakage between tasks
        
        system_prompt = f"""
        You are an autonomous coding agent. You can execute bash commands to explore the environment, read files, and write code. 
        The current project is: {project_name}
        
        Available Tools:
        - Execute Bash: Use the format <bash>command</bash>
        - Finish: Use the format <finish>result summary</finish>
        
        Rules:
        1. Analyze the request and plan a series of steps.
        2. If you use <bash>, the system will execute it and provide you with the output. 
        3. Only one bash command per turn. 
        4. Once you are confident in your result, use <finish> to report back.
        """

        context = f"Task: {instructions}\n\n"
        current_turn = 0
        max_turns = 20

        while current_turn < max_turns:
            current_turn += 1
            
            # Prepare the prompt with history
            full_prompt = f"""
            Current Turn: {current_turn}
            {context}
            

History:
{"".join(history)}

"""
            
            response = self.llm.generate_response(full_prompt, system_prompt=system_prompt)
            
            if "<finish>" in response:
                final_report = response.split("<finish>")[1].split("</finish>")[1] if "</finish>" in response else response.split("<finish>")[1]
                return final_report
            
            if "<bash>" in response:
                command = response.split("<bash>")[1].split("</bash>")[0]
                result = self.execute_bash(command, cwd=cwd)
                history.append(f"\nTurn {current_turn}: Agent requested <bash>{command}</bash>\nOutput: {result['stdout']}\nError: {result['stderr']}\nExit Code: {result['exit_code']}\n")
            else:
                history.append(f"\nTurn {current_turn}: Agent thought process: {response}\n")

        return "Reached maximum turns without finishing."

    def start(self):
        """
        Entry point for the agent to monitor emails and process tasks.
        """
        print("Monitoring emails... (Press Ctrl+C to stop)")
        while True:
            tasks = self.email_handler.fetch_new_emails()
            if not tasks:
                print("No new tasks found. Waiting... ")
            else:
                for task in tasks:
                    print(f"Processing task: {task['project']} from {task['sender']}")
                    final_report = self.run_task(task)
                    self.email_handler.send_email(
                        recipient=task['sender'],
                        subject=f"Re: {task['subject']}",
                        body=final_report
                    )
            time.sleep(60) # Poll every minute
