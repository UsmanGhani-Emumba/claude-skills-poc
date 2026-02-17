import json
import time
import os
import sys
import importlib.util
from pathlib import Path
from opentelemetry import trace
from src.agents.base import BaseAgent, client
from src.config import Config

# Add .gemini/skills to sys.path to allow importing base
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.gemini', 'skills'))
from base import BaseSkill

tracer = trace.get_tracer(__name__)

class Orchestrator(BaseAgent):
    def __init__(self):
        super().__init__(name="Orchestrator")
        self.project_skills_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'skills')
        self.gemini_skills_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.gemini', 'skills')
        self.skills = {}
        self._load_all_skills()

    def _load_all_skills(self):
        """Discovers and loads all skills from both standard and project directories."""
        for path in [self.gemini_skills_path, self.project_skills_path]:
            if not os.path.exists(path):
                continue
            for skill_name in os.listdir(path):
                skill_dir = os.path.join(path, skill_name)
                if not os.path.isdir(skill_dir) or skill_name == "__pycache__":
                    continue
                
                # Try to find a reference implementation
                ref_dir = os.path.join(skill_dir, 'references')
                skill_class = None
                
                if os.path.exists(ref_dir):
                    for ref_file in os.listdir(ref_dir):
                        if ref_file.endswith('.py'):
                            skill_class = self._load_skill_class(os.path.join(ref_dir, ref_file), skill_name)
                            if skill_class:
                                break
                
                if skill_class:
                    try:
                        # Instantiate the skill
                        self.skills[skill_name] = skill_class(client=client, model=self.model_name)
                    except Exception as e:
                        print(f"Warning: Could not instantiate skill {skill_name}: {e}")
                else:
                    # Fallback: create a dynamic skill if no class found but SKILL.md exists
                    if os.path.exists(os.path.join(skill_dir, 'SKILL.md')):
                        self.skills[skill_name] = self._create_dynamic_skill(skill_name)

    def _load_skill_class(self, file_path, skill_name):
        try:
            spec = importlib.util.spec_from_file_location(f"skill_{skill_name}", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            for attr in dir(module):
                obj = getattr(module, attr)
                if isinstance(obj, type) and issubclass(obj, BaseSkill) and obj is not BaseSkill:
                    return obj
        except Exception as e:
            # print(f"Note: Could not load skill class from {file_path}: {e}")
            pass
        return None

    def _create_dynamic_skill(self, skill_name):
        class DynamicSkill(BaseSkill):
            @property
            def name(self): return skill_name
            @property
            def _fallback_prompt(self): return f"You are the {skill_name} skill."
        return DynamicSkill(client=client, model=self.model_name)

    def _get_skill_context(self, skill_name: str) -> str:
        """Loads additional references for the skill if they exist."""
        # Find skill directory
        skill_dir = os.path.join(self.project_skills_path, skill_name)
        if not os.path.exists(skill_dir):
            skill_dir = os.path.join(self.gemini_skills_path, skill_name)
        
        context = ""
        # Load references if they exist
        ref_dir = os.path.join(skill_dir, 'references')
        if os.path.exists(ref_dir):
            for ref_file in os.listdir(ref_dir):
                if ref_file.endswith('.md'):
                    with open(os.path.join(ref_dir, ref_file), 'r', encoding='utf-8') as f:
                        context += f"\n--- Reference: {ref_file} ---\n"
                        context += f.read()
        
        # Add special environment context for publisher
        if "publisher" in skill_name:
            context += f"\n--- Environment Context ---\n"
            context += f"NOTION_API_KEY: {Config.NOTION_API_KEY}\n"
            context += f"NOTION_PARENT_PAGE_ID: {Config.NOTION_PARENT_PAGE_ID}\n"

        return context

    def _execute(self, user_input: str) -> str:
        print(f"\n--- Orchestrator Analyzing Intent: '{user_input}' ---\n")

        intent_prompt = f"""
        Analyze the following user request and determine which skills are needed to fulfill it.
        Available Skills: {list(self.skills.keys())}

        If the user wants a full blog post from scratch, the sequence is: blog-researcher -> blog-writer -> blog-reviewer -> blog-publisher.
        If the user only wants specific tasks, only include those.

        Return a JSON list of objects representing the plan.
        Example: [{{"skill": "blog-researcher", "task": "..."}}]
        
        User Request: {user_input}
        """
        
        plan_json = self.generate_text(intent_prompt)
        try:
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

        context_data = user_input
        final_result = ""

        for step in plan:
            skill_name = step['skill']
            task_description = step.get('task', f"Execute {skill_name}")
            
            if skill_name not in self.skills:
                print(f"Warning: Skill {skill_name} not found. Skipping.")
                continue

            print(f"\n--- Triggering Skill: {skill_name} ---\n")
            
            skill_instance = self.skills[skill_name]
            skill_extra_context = self._get_skill_context(skill_name)
            
            start_time = time.time()
            status = "Pass"
            
            with tracer.start_as_current_span(name=f"Skill.{skill_name}") as span:
                span.set_attribute("skill.name", skill_name)
                span.set_attribute("skill.task", task_description)
                
                try:
                    # Execute skill using its own logic
                    full_context = {"previous_step_data": context_data, "extra_info": skill_extra_context}
                    result_dict = skill_instance.execute(task_description, context=full_context)
                    
                    output = result_dict["content"]
                    context_data = output 
                    final_result = output
                    span.set_status(trace.Status(trace.StatusCode.OK))
                except Exception as e:
                    status = "Fail"
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    print(f"Error executing skill {skill_name}: {e}")
                    break 
                finally:
                    latency = time.time() - start_time
                    metrics = {
                        "skill": skill_name,
                        "status": status,
                        "latency_sec": round(latency, 2)
                    }
                    print(f"[METRICS] {json.dumps(metrics)}")

        print("\n--- Orchestration Complete ---\n")
        return final_result
