
import time
from agent_loop import AgentLoop

if __name__ == "__main__":
    agent = AgentLoop()
    try:
        agent.start()
    except KeyboardInterrupt:
        print("Stopping Codemail system...")
