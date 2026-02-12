/* notion-publish.js */
const https = require('https');
const fs = require('fs');
const path = require('path');

const NOTION_TOKEN = process.env.NOTION_TOKEN;
const PARENT_ID = process.env.NOTION_PARENT_ID;
const CONTENT_FILE = process.env.CONTENT_FILE || 'blog_content.json';

if (!NOTION_TOKEN || !PARENT_ID) {
  console.error('Error: NOTION_TOKEN and NOTION_PARENT_ID must be set.');
  process.exit(1);
}

async function request(options, body) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          if (res.statusCode >= 400) reject(json);
          else resolve(json);
        } catch (e) {
          reject(data);
        }
      });
    });
    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function publish() {
  const contentPath = path.isAbsolute(CONTENT_FILE) ? CONTENT_FILE : path.join(process.cwd(), CONTENT_FILE);
  if (!fs.existsSync(contentPath)) {
    throw new Error(`Content file not found at: ${contentPath}`);
  }
  
  const blog = JSON.parse(fs.readFileSync(contentPath, 'utf8'));

  console.log(`🚀 Creating page: ${blog.title}`);
  
  const page = await request({
    hostname: 'api.notion.com',
    path: '/v1/pages',
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${NOTION_TOKEN}`,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json'
    }
  }, {
    parent: { page_id: PARENT_ID },
    properties: {
      title: [{ text: { content: blog.title } }]
    }
  });

  const pageId = page.id;
  console.log(`✅ Page created! ID: ${pageId}`);

  // Transform blocks
  const blocks = blog.blocks.map(b => {
    if (b.type === 'divider') return { object: 'block', type: 'divider', divider: {} };
    return {
      object: 'block',
      type: b.type,
      [b.type]: {
        rich_text: [{ type: 'text', text: { content: b.content } }]
      }
    };
  });

  // Batch upload (5 blocks per call)
  const batchSize = 5;
  for (let i = 0; i < blocks.length; i += batchSize) {
    const batch = blocks.slice(i, i + batchSize);
    console.log(`📤 Uploading batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(blocks.length / batchSize)}...`);
    
    await request({
      hostname: 'api.notion.com',
      path: `/v1/blocks/${pageId}/children`,
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${NOTION_TOKEN}`,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
      }
    }, { children: batch });
  }

  console.log(`\n🎉 Published successfully!`);
  console.log(`URL: ${page.url}`);
}

publish().catch(err => {
  console.error('❌ Failed:', JSON.stringify(err, null, 2));
  process.exit(1);
});
