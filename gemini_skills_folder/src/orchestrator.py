from src.agents.base import BaseAgent
import json
import time
from phoenix.trace import tracer

class Orchestrator(BaseAgent):
    def __init__(self):
        super().__init__(name="Orchestrator")

    def _execute(self, user_input: str) -> str:
        """
        Identifies user intent and orchestrates the necessary skills with metrics logging.
        """
        print(f"\n--- Orchestrator Analyzing Intent: '{user_input}' ---\n")

        # 1. Intent Detection Phase
        intent_prompt = f"""
        Analyze the following user request and determine which skills are needed to fulfill it.
        Available Skills:
        - blog-researcher: Used for gathering data and sub-topics.
        - blog-writer: Used for drafting content based on research.
        - blog-reviewer: Used for polishing and humanizing content.
        - blog-publisher: Used for sending content to Notion.

        If the user wants a full blog post from scratch, the sequence is: researcher -> writer -> reviewer -> publisher.
        If the user only wants specific tasks, only include those.

        Return a JSON list of objects representing the plan.
        Example: [{"skill": "blog-researcher", "task": "..."}]
        
        User Request: {user_input}
        """
        
        plan_json = self.generate_text(intent_prompt)
        try:
            # Cleanup JSON block
            cleaned_json = plan_json.strip()
            if "```json" in cleaned_json:
                cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_json:
                cleaned_json = cleaned_json.split("```")[1].split("```")[0].strip()
            
            plan = json.loads(cleaned_json)
        except Exception as e:
            print(f"Error parsing intent plan: {e}")
            return f"I couldn't determine a plan for your request. Model output: {plan_json}"

        print(f"Identified Plan: {[step['skill'] for step in plan]}")

        # 2. Execution Phase
        context_data = user_input
        final_result = ""

        for step in plan:
            skill_name = step['skill']
            task_description = step.get('task', f"Execute {skill_name}")
            
            print(f"\n--- Triggering Skill: {skill_name} ---\n")
            
            start_time = time.time()
            status = "Pass"
            
            with tracer().start_span(name=f"Skill.{skill_name}") as span:
                span.set_attribute("skill.name", skill_name)
                span.set_attribute("skill.task", task_description)
                
                try:
                    # Formulate the prompt for the specific skill
                    skill_trigger_prompt = f"Act as the '{skill_name}' skill. Your task is: {task_description}. Use this context/data: {context_data}"
                    
                    # Execute
                    output = self.generate_text(skill_trigger_prompt)
                    
                    # Update context for the next skill (Chaining)
                    context_data = output 
                    final_result = output
                    span.set_status(status_code="OK")
                except Exception as e:
                    status = "Fail"
                    span.set_status(status_code="ERROR", description=str(e))
                    print(f"Error executing skill {skill_name}: {e}")
                    break # Stop pipeline on failure
                finally:
                    latency = time.time() - start_time
                    # Print metrics for console visibility (Arize logic)
                    metrics = {
                        "skill": skill_name,
                        "status": status,
                        "latency_sec": round(latency, 2)
                    }
                    print(f"[METRICS] {json.dumps(metrics)}")

        print("\n--- Orchestration Complete ---\n")
        return final_result