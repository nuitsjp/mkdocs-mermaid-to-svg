import { renderMermaid, THEMES, DEFAULTS } from 'beautiful-mermaid'

const args = process.argv.slice(2)
const mode = args[0]

const readStdin = async () =>
  new Promise((resolve, reject) => {
    let data = ''
    process.stdin.setEncoding('utf8')
    process.stdin.on('data', chunk => {
      data += chunk
    })
    process.stdin.on('end', () => resolve(data))
    process.stdin.on('error', err => reject(err))
  })

const exitWith = (message, code = 1) => {
  if (message) {
    process.stderr.write(`${message}\n`)
  }
  process.exit(code)
}

const themeMap = {
  dark: 'zinc-dark',
}

/** テーマ名を解決してbeautiful-mermaidのテーマオブジェクトを返す */
const resolveTheme = (themeName) => {
  const name = themeName ?? 'default'
  const resolvedName = themeMap[name] ?? name
  return THEMES[resolvedName] ?? DEFAULTS
}

if (mode === '--check') {
  process.exit(0)
}

if (mode === '--batch-render') {
  try {
    const payloadRaw = await readStdin()
    const items = JSON.parse(payloadRaw || '[]')
    const results = []
    for (const item of items) {
      try {
        const code = item.code ?? ''
        if (!code.trim()) {
          results.push({ id: item.id, success: false, error: 'Mermaidコードが空です' })
          continue
        }
        const baseTheme = resolveTheme(item.theme)
        const renderOptions = { ...baseTheme, ...(item.options || {}) }
        const svg = await renderMermaid(code, renderOptions)
        results.push({ id: item.id, success: true, svg })
      } catch (err) {
        results.push({ id: item.id, success: false, error: err?.message ?? String(err) })
      }
    }
    process.stdout.write(JSON.stringify(results))
  } catch (err) {
    exitWith(err?.message ?? String(err), 1)
  }
} else if (mode === '--render') {
  try {
    const payloadRaw = await readStdin()
    const payload = JSON.parse(payloadRaw || '{}')
    const code = payload.code ?? ''
    if (!code.trim()) {
      exitWith('Mermaidコードが空です', 2)
    }
    const baseTheme = resolveTheme(payload.theme)
    const renderOptions = { ...baseTheme, ...(payload.options || {}) }
    const svg = await renderMermaid(code, renderOptions)
    process.stdout.write(svg)
  } catch (err) {
    exitWith(err?.message ?? String(err), 1)
  }
} else {
  exitWith('使い方: beautiful_mermaid_runner.mjs --check|--render|--batch-render', 2)
}
