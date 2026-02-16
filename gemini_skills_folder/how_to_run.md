# How to Run the Gemini Skill Orchestrator

This guide provides step-by-step instructions to set up the environment and run the orchestrator POC.

## 1. Prerequisites
- **Python 3.11.5** (Required for Arize Phoenix compatibility).
- **Git** (For repository management).

## 2. Environment Setup

### Create a Virtual Environment
Using PowerShell (Windows) with the Python Launcher:
```powershell
# Create the environment explicitly using Python 3.11
py -3.11 -m venv venv

# If 'py' is not available, use the direct path to your 3.11 executable:
# C:\Path\To\Python311\python.exe -m venv venv

# Activate the environment
.\venv\Scripts\Activate
```

### Install Dependencies
Once the environment is active, install the required libraries:
```powershell
pip install -r requirements.txt
```

## 3. Configuration
1. Create a `.env` file in the root directory.
2. Add your API keys and configuration:
```env
GEMINI_API_KEY=your_google_gemini_api_key
NOTION_API_KEY=your_notion_integration_token
NOTION_PARENT_PAGE_ID=2ff01e7f802c8041bb7bf826722f02da
ARIZE_SPACE_KEY=your_arize_space_key
ARIZE_API_KEY=your_arize_api_key
```

## 4. Packaging and Installing Skills
Before running the agent, you must package and install the custom skills.

### Package Skills
```powershell
mkdir dist
node "C:\Users\Emumba\AppData\Roaming
pm
ode_modules\@google\gemini-cli
ode_modules\@google\gemini-cli-core\dist\src\skills\builtin\skill-creator\scripts\package_skill.cjs" skills\blog-researcher dist
node "C:\Users\Emumba\AppData\Roaming
pm
ode_modules\@google\gemini-cli
ode_modules\@google\gemini-cli-core\dist\src\skills\builtin\skill-creator\scripts\package_skill.cjs" skills\blog-writer dist
node "C:\Users\Emumba\AppData\Roaming
pm
ode_modules\@google\gemini-cli
ode_modules\@google\gemini-cli-core\dist\src\skills\builtin\skill-creator\scripts\package_skill.cjs" skills\blog-reviewer dist
node "C:\Users\Emumba\AppData\Roaming
pm
ode_modules\@google\gemini-cli
ode_modules\@google\gemini-cli-core\dist\src\skills\builtin\skill-creator\scripts\package_skill.cjs" skills\blog-publisher dist
```

### Install Skills
```powershell
gemini skills install dist\blog-researcher.skill --scope workspace
gemini skills install dist\blog-writer.skill --scope workspace
gemini skills install dist\blog-reviewer.skill --scope workspace
gemini skills install dist\blog-publisher.skill --scope workspace
```

### Reload Skills
In your interactive Gemini CLI session, run:
```bash
/skills reload
```

## 5. Running the Agent
Execute the main orchestrator script:
```powershell
python main.py
```

### Observability
When the script starts, it will launch **Arize Phoenix**. 
- Open the provided URL (usually `http://localhost:6006`) to view real-time traces, latency, and token metrics for each skill execution.

## 6. Usage Examples
Once the agent is running, you can provide prompts like:
- "Research and publish a blog post about the impact of Generative AI on software testing."
- "Just research current trends in climate tech for 2026."
- "Publish this draft to Notion: [Your Content Here]"
