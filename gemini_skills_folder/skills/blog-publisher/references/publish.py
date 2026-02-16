import sys
import json
import time
import argparse
from notion_client import Client

def log_to_arize(name, status, start_time, blocks_count):
    latency = time.time() - start_time
    metrics = {
        "span_name": name,
        "latency_sec": round(latency, 2),
        "blocks_published": blocks_count,
        "status": status
    }
    print(f"METRICS_LOG: {json.dumps(metrics)}")

def publish_to_notion(token, parent_id, title, content):
    notion = Client(auth=token)
    start_time = time.time()
    blocks_count = 0
    
    try:
        # 1. Identify/Verify parent
        try:
            notion.pages.retrieve(page_id=parent_id)
        except:
            try:
                notion.databases.retrieve(database_id=parent_id)
            except:
                return f"Error: Parent ID {parent_id} not found or not shared with integration."

        # 2. Create the page
        new_page = notion.pages.create(
            parent={"page_id": parent_id},
            properties={"title": [{"text": {"content": title}}]}
        )
        page_id = new_page["id"]
        
        # 3. Process blocks
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

        # 4. Batch push with 429 retry
        batch_size = 50
        blocks_count = len(blocks)
        for i in range(0, blocks_count, batch_size):
            batch = blocks[i:i + batch_size]
            retries = 5
            wait_time = 2
            success = False
            while retries > 0 and not success:
                try:
                    notion.blocks.children.append(block_id=page_id, children=batch)
                    success = True
                except Exception as e:
                    if "429" in str(e):
                        time.sleep(wait_time)
                        retries -= 1
                        wait_time *= 2
                    else:
                        raise e
            if not success:
                raise Exception("Failed after multiple 429 retries.")
            time.sleep(0.3)

        log_to_arize("publish_notion", "Pass", start_time, blocks_count)
        return f"https://www.notion.so/{page_id.replace('-', '')}"
    except Exception as e:
        log_to_arize("publish_notion", "Fail", start_time, blocks_count)
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
    print(publish_to_notion(args.token, args.parent, args.title, content))