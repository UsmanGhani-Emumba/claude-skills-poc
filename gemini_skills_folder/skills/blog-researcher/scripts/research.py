import sys, json, time, argparse, requests
from bs4 import BeautifulSoup
from googlesearch import search
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

def log_to_arize(name, status, start_time, tokens_in, tokens_out):
    latency = time.time() - start_time
    metrics = {
        "span_name": name,
        "latency_sec": round(latency, 2),
        "input_tokens": tokens_in,
        "output_tokens": tokens_out,
        "status": status,
        "cost_est": round((tokens_in * 0.000125 + tokens_out * 0.000375) / 1000, 6)
    }
    print(f"METRICS_LOG: {json.dumps(metrics)}")

class ResearchTools:
    @staticmethod
    def web_search(query, num_results=5):
        try:
            return list(search(query, num_results=num_results))
        except:
            try: return list(search(query, num=num_results, stop=num_results, pause=2))
            except: return []

    @staticmethod
    def scrape_article(url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, timeout=10, headers=headers)
            soup = BeautifulSoup(res.content, 'html.parser')
            text = "\n".join([p.get_text() for p in soup.find_all('p')])
            return text[:4000] if text else "No content found."
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def get_youtube(url):
        try:
            parsed = urlparse(url)
            v_id = None
            if parsed.hostname == 'youtu.be': v_id = parsed.path[1:]
            elif 'youtube.com' in parsed.hostname:
                if parsed.path == '/watch': v_id = parse_qs(parsed.query).get('v', [None])[0]
                elif '/embed/' in parsed.path: v_id = parsed.path.split('/')[-1]
            
            if not v_id: return "Error: No Video ID extracted."
            transcript = YouTubeTranscriptApi.get_transcript(v_id)
            return " ".join([t['text'] for t in transcript])[:4000]
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def get_github(query):
        """Search GitHub for repositories or content."""
        try:
            url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc"
            res = requests.get(url, timeout=10)
            data = res.json()
            items = data.get('items', [])[:5]
            results = []
            for item in items:
                results.append({
                    "name": item['full_name'],
                    "description": item['description'],
                    "url": item['html_url'],
                    "stars": item['stargazers_count']
                })
            return json.dumps(results, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool", required=True, choices=["search", "scrape", "youtube", "github"])
    parser.add_argument("--query", required=True)
    args = parser.parse_args()
    
    start_time = time.time()
    res = ""
    status = "Pass"
    
    try:
        if args.tool == "search": res = json.dumps(ResearchTools.web_search(args.query))
        elif args.tool == "scrape": res = ResearchTools.scrape_article(args.query)
        elif args.tool == "youtube": res = ResearchTools.get_youtube(args.query)
        elif args.tool == "github": res = ResearchTools.get_github(args.query)
        
        if res.startswith("Error"): status = "Fail"
    except Exception as e:
        res = f"Error: {str(e)}"
        status = "Fail"

    # Token estimation
    t_in = int(len(args.query.split()) * 1.5)
    t_out = int(len(res.split()) * 1.5)
    log_to_arize(f"research_{args.tool}", status, start_time, t_in, t_out)
    
    print("\n---RESULT_START---")
    print(res)
    print("---RESULT_END---")

if __name__ == "__main__":
    main()
