import sys
import json
import time
import argparse
from notion_client import Client

def log_to_arize(name, status, start_time, blocks_count, error_msg=""):
    latency = time.time() - start_time
    metrics = {
        "span_name": name,
        "latency_sec": round(latency, 2),
        "blocks_published": blocks_count,
        "status": status,
        "error": error_msg
    }
    print(f"METRICS_LOG: {json.dumps(metrics)}")

def publish_to_notion(token, parent_id, title, content):
    notion = Client(auth=token)
    start_time = time.time()
    blocks_count = 0
    
    try:
        # STEP 1: Identify/Verify parent page via ID
        print(f"STEP 1: Verifying parent page ID: {parent_id}")
        try:
            notion.pages.retrieve(page_id=parent_id)
        except Exception as e:
            msg = f"Parent page verification failed: {str(e)}"
            log_to_arize("publish_notion", "Fail", start_time, 0, msg)
            return f"Error: {msg}"

        # STEP 2: Create an empty page with blog title under parent
        print(f"STEP 2: Creating empty page '{title}' under parent...")
        try:
            new_page = notion.pages.create(
                parent={"page_id": parent_id},
                properties={"title": [{"text": {"content": title}}]}
            )
            page_id = new_page["id"]
        except Exception as e:
            msg = f"Page creation failed: {str(e)}"
            log_to_arize("publish_notion", "Fail", start_time, 0, msg)
            return f"Error: {msg}"
        
        # STEP 3: Add blocks to the newly created page with auto-batching
        print("STEP 3: Processing and adding content blocks...")
        
        # Convert Markdown-ish content to Notion blocks
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        blocks = []
        for line in lines:
            block_type = "paragraph"
            text_content = line
            if line.startswith("# "):
                block_type = "heading_1"
                text_content = line[2:]
            elif line.startswith("## "):
                block_type = "heading_2"
                text_content = line[3:]
            elif line.startswith("### "):
                block_type = "heading_3"
                text_content = line[4:]
            
            blocks.append({
                "object": "block",
                "type": block_type,
                block_type: {"rich_text": [{"text": {"content": text_content[:2000]}}]}
            })

        # Notion Standard: Max 100 blocks per request. Using 50 for safety.
        batch_size = 50
        blocks_count = len(blocks)
        
        for i in range(0, blocks_count, batch_size):
            batch = blocks[i:i + batch_size]
            
            # Resilience logic for 429 Rate Limits
            retries = 5
            wait_time = 2
            success = False
            
            while retries > 0 and not success:
                try:
                    notion.blocks.children.append(block_id=page_id, children=batch)
                    success = True
                except Exception as e:
                    if "429" in str(e):
                        print(f"429 Rate Limit hit. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        retries -= 1
                        wait_time *= 2
                    else:
                        raise e
            
            if not success:
                msg = f"Batching failed at block {i} after multiple 429 retries."
                log_to_arize("publish_notion", "Fail", start_time, i, msg)
                return f"Error: {msg}"
            
            time.sleep(0.3) # Buffer for Notion stability

        log_to_arize("publish_notion", "Pass", start_time, blocks_count)
        return f"https://www.notion.so/{page_id.replace('-', '')}"

    except Exception as e:
        log_to_arize("publish_notion", "Fail", start_time, 0, str(e))
        return f"Error: {str(e)}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--parent", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--content_file", required=True)
    args = parser.parse_args()
    
    with open(args.content_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    result = publish_to_notion(args.token, args.parent, args.title, content)
    print(f"PUBLISH_RESULT: {result}")
