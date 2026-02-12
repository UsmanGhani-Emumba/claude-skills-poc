import sys
import os
import subprocess
import json
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

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/orchestrator_gemini.py <topic>")
        sys.exit(1)
        
    topic = sys.argv[1]
    print(f"🎬 Starting Content Engine for: {topic}")
    
    # 1. Start Global Session (if needed, or just per skill)
    # We'll use the topic as a way to group traces in Arize Phoenix
    
    # Phase 1: Researcher
    research_task = f"Research the following topic for a blog post: {topic}. Break it down into sub-topics and find key facts, statistics, and recent developments. Use web_fetch and github_cli where appropriate."
    research_brief, r_metrics = run_skill("researcher", research_task, topic)
    
    # Phase 2: Writer
    write_task = f"Write a blog post about {topic} based on this research brief:\n\n{research_brief}\n\nTarget audience: Technical practitioners."
    draft, w_metrics = run_skill("writer", write_task, topic)
    
    # Phase 3: Reviewer
    review_task = f"Review the following blog draft for quality, accuracy, and style:\n\n{draft}\n\nEnsure sources are bulleted and the tone is appropriate."
    final_blog, rev_metrics = run_skill("reviewer", review_task, topic)
    
    # Phase 4: Publisher
    publish_task = f"AUTONOMOUS ACTION: Discover the 'Gemini Workspace' and publish this blog post to Notion immediately. Do not ask for confirmation.\n\n{final_blog}"
    p_status, p_metrics = run_skill("publisher", publish_task, topic)
    
    print("\n✅ Content Engine Run Complete!")
    print(f"Topic: {topic}")
    print(f"Total Latency: {r_metrics.get('latency_seconds', 0) + w_metrics.get('latency_seconds', 0) + rev_metrics.get('latency_seconds', 0) + p_metrics.get('latency_seconds', 0)}s")

if __name__ == "__main__":
    main()
