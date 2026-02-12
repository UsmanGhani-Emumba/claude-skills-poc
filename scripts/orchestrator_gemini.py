import sys
import os
import subprocess
import json
import argparse
from pathlib import Path

def run_skill(skill, task, topic, session_id=None):
    print(f"\n🚀 Running Skill: {skill}")
    project_name = f"{topic.replace(' ', '_')}_gemini_skills"
    
    cmd = [
        sys.executable, "scripts/gemini_skills_analyzer.py",
        "--skill", skill,
        "--task", task,
        "--project-name", project_name
    ]
    if session_id:
        cmd.extend(["--session-id", session_id])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Extract JSON from stdout (skip Arize headers)
    stdout = result.stdout
    try:
        if "{" in stdout:
            json_str = stdout[stdout.find("{") : stdout.rfind("}") + 1]
            data = json.loads(json_str)
            return data.get("result", ""), data.get("metrics", {})
        else:
            raise ValueError("No JSON found in stdout")
    except Exception as e:
        print(f"Error parsing {skill} output: {e}\nFull Output: {stdout}\nStderr: {result.stderr}")
        return "", {}

def detect_intent(prompt):
    """Refined intent detection. We prioritize standalone skills unless 'blog/engine' is clear."""
    p = prompt.lower()
    
    # 2. Sequential/Composite Intent
    if any(k in p for k in ["publish", "deploy", "notion"]):
        # If they want to write/research AND publish, they likely want the engine
        if any(k in p for k in ["write", "draft", "author"]):
            return "content_engine"
        # If it's just 'publish research', it goes to publisher (assuming research text is provided)
        return "publisher"
    
    # 3. Standalone Skill Triggers
    if any(k in p for k in ["research", "find", "search", "brief", "facts"]):
        return "researcher"
    if any(k in p for k in ["write", "draft", "author", "create"]):
        return "writer"
    if any(k in p for k in ["review", "critique", "check", "edit"]):
        return "reviewer"
    
    # Default to researcher for data gathering if intent is vague
    return "researcher"

def main():
    parser = argparse.ArgumentParser(
        description="Dynamic Gemini Skill Orchestrator",
        epilog="Example: python scripts/orchestrator_gemini.py \"Research Playwright\" --topic automation"
    )
    parser.add_argument("prompt", help="The user prompt or task description.")
    parser.add_argument("--skill", help="Explicitly specify a skill to run (researcher, writer, reviewer, publisher, content_engine).")
    parser.add_argument("--topic", help="Topic name for metrics grouping and session tracking.")
    args = parser.parse_args()

    prompt = args.prompt
    topic = args.topic or prompt.split(":")[0][:50]
    
    # Decide which skill/pipeline to run
    target_skill = args.skill or detect_intent(prompt)
    
    print(f"🎬 Starting Orchestrator for: {prompt}")
    print(f"🎯 Target: {target_skill.upper()}")

    if target_skill == "content_engine":
        # Full Pipeline
        research_task = f"Research the following topic for a blog post: {prompt}. Break it down into sub-topics and find key facts, statistics, and recent developments."
        research_brief, r_m = run_skill("researcher", research_task, topic)
        
        write_task = f"Write a blog post about {topic} based on this research brief:\n\n{research_brief}"
        draft, w_m = run_skill("writer", write_task, topic)
        
        review_task = f"Review the following blog draft:\n\n{draft}"
        final_blog, rv_m = run_skill("reviewer", review_task, topic)
        
        publish_task = f"AUTONOMOUS ACTION: Publish this blog post to Notion (Gemini Workspace):\n\n{final_blog}"
        p_status, p_m = run_skill("publisher", publish_task, topic)
        
        total_latency = r_m.get('latency_seconds',0) + w_m.get('latency_seconds',0) + rv_m.get('latency_seconds',0) + p_m.get('latency_seconds',0)
    else:
        # Single Skill Execution
        status, metrics = run_skill(target_skill, prompt, topic)
        total_latency = metrics.get('latency_seconds', 0)
        print(f"\nResult:\n{status}")

    print("\n✅ Execution Complete!")
    print(f"Total Latency: {total_latency:.2f}s")

if __name__ == "__main__":
    main()
