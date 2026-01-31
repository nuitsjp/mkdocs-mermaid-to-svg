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

if (mode === '--check') {
  process.exit(0)
}

if (mode !== '--render') {
  exitWith('使い方: beautiful_mermaid_runner.mjs --check|--render', 2)
}

try {
  const payloadRaw = await readStdin()
  const payload = JSON.parse(payloadRaw || '{}')
  const code = payload.code ?? ''
  if (!code.trim()) {
    exitWith('Mermaidコードが空です', 2)
  }
  const themeMap = {
    dark: 'zinc-dark',
  }
  const themeName = payload.theme ?? 'default'
  const resolvedName = themeMap[themeName] ?? themeName
  const theme = THEMES[resolvedName] ?? DEFAULTS
  const svg = await renderMermaid(code, theme)
  process.stdout.write(svg)
} catch (err) {
  exitWith(err?.message ?? String(err), 1)
}
