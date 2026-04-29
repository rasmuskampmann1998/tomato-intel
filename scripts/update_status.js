#!/usr/bin/env node
// Fetches live Supabase row counts and rewrites the scraper data section of tomato-intel-status.md
// Run manually or triggered via Claude Code SessionStart hook

const https = require('https')
const fs = require('fs')
const path = require('path')

const SUPABASE_URL = 'https://evifsyqtrwwetfqkvlni.supabase.co'
const SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV2aWZzeXF0cnd3ZXRmcWt2bG5pIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzI5MDU3MSwiZXhwIjoyMDkyODY2NTcxfQ.yn1ZqcnV7dAqV-4VsaZWbafnDno72rqblJcVX1kc6tk'
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV2aWZzeXF0cnd3ZXRmcWt2bG5pIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcyOTA1NzEsImV4cCI6MjA5Mjg2NjU3MX0.Ku7lNHEbYSFXKFAmIWkBH_cj7YiqE5ZhMK2rQ3RFxKI'

const STATUS_FILE = path.join(
  'C:\\Users\\rasmu\\.claude\\projects\\c--Users-rasmu-OneDrive-Digi-tal-Outbound-Programs-N8n\\memory\\tomato-intel-status.md'
)

function get(table, useServiceKey = true) {
  return new Promise((resolve) => {
    const key = useServiceKey ? SERVICE_KEY : ANON_KEY
    const urlObj = new URL(`${SUPABASE_URL}/rest/v1/${table}`)
    urlObj.searchParams.set('select', '*')
    urlObj.searchParams.set('limit', '0')
    const req = https.request(urlObj.toString(), {
      method: 'GET',
      headers: {
        apikey: key,
        Authorization: `Bearer ${key}`,
        Prefer: 'count=exact',
        Range: '0-0',
      },
    }, (res) => {
      let body = ''
      res.on('data', d => { body += d })
      res.on('end', () => {
        // Content-Range: 0-0/TOTAL or */TOTAL
        const range = res.headers['content-range'] || ''
        const match = range.match(/\/(\d+)$/)
        const count = match ? parseInt(match[1], 10) : -1
        resolve({ table, count, status: res.statusCode })
      })
    })
    req.on('error', () => resolve({ table, count: -1, status: 0 }))
    req.end()
  })
}

async function main() {
  const today = new Date().toISOString().slice(0, 10)

  const [categories, sources, scraped, profiles, interpreted] = await Promise.all([
    get('categories'),
    get('sources'),
    get('scraped_items'),
    get('search_profiles'),
    get('interpreted_items'),
  ])

  // Test anon read to check if RLS blocker is resolved
  const anonTest = await get('categories', false)
  const rlsResolved = anonTest.status === 200 && anonTest.count > 0

  const status = fs.readFileSync(STATUS_FILE, 'utf8')

  // Update scraper data section
  const scrapedSection = `## Scraper Data State (${today})
${scraped.count} items in \`scraped_items\` | ${interpreted.count} interpreted | ${sources.count} sources | ${profiles.count} search profiles | ${categories.count} categories`

  let updated = status.replace(
    /## Scraper Data State \([^)]+\)[\s\S]*?(?=\n## |\n$|$)/,
    scrapedSection + '\n'
  )

  // Update RLS blocker status if resolved
  if (rlsResolved) {
    updated = updated.replace(
      /\*\*BLOCKER — RLS Policies[\s\S]*?\*\*(.*?)(?=\n## )/,
      (match) => match // preserve existing if already says RESOLVED
    )
    if (!updated.includes('RESOLVED')) {
      updated = updated.replace(
        '## BLOCKER — RLS Policies (UX shows empty data)',
        `## ✅ RLS Fixed (${today}) — anon reads working`
      )
    }
  }

  fs.writeFileSync(STATUS_FILE, updated, 'utf8')
  console.log(`[update_status] ${today} — scraped:${scraped.count} sources:${sources.count} profiles:${profiles.count} RLS:${rlsResolved ? 'OK' : 'BLOCKED'}`)
}

main().catch(console.error)
