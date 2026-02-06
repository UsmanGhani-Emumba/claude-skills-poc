/* notion-discover.js */
const https = require('https');

const NOTION_TOKEN = process.env.NOTION_TOKEN;

if (!NOTION_TOKEN) {
  console.error('Error: NOTION_TOKEN environment variable is not set.');
  process.exit(1);
}

const req = https.request({
  hostname: 'api.notion.com',
  path: '/v1/search',
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${NOTION_TOKEN}`,
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json'
  }
}, (res) => {
  let data = '';
  res.on('data', (chunk) => data += chunk);
  res.on('end', () => {
    try {
      const json = JSON.parse(data);
      if (res.statusCode >= 400) {
        console.error('API Error:', JSON.stringify(json, null, 2));
        process.exit(1);
      }
      // Output clean list for agent to parse
      json.results.forEach(page => {
        const title = page.properties.title ? page.properties.title.title.map(t => t.plain_text).join('') : 'Untitled';
        console.log(`[${page.id}] ${title}`);
      });
    } catch (e) {
      console.error('Parse Error:', data);
      process.exit(1);
    }
  });
});

req.on('error', (e) => {
  console.error('Request Error:', e.message);
  process.exit(1);
});

req.write(JSON.stringify({ filter: { property: 'object', value: 'page' }, page_size: 20 }));
req.end();
