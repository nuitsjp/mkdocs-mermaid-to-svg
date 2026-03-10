/**
 * Puppeteer常駐プロセスによるMermaidレンダリングスクリプト
 *
 * mmdcの`renderMermaid`関数(L247-280)を参考に、同等のレンダリングを実装。
 * ブラウザを1回起動し、NDJSONプロトコルで複数リクエストを処理する。
 *
 * 起動: node persistent_mermaid_renderer.mjs <base64-encoded-startup-config-json>
 */

import puppeteer from 'puppeteer'
import { createRequire } from 'node:module'
import { resolve as importMetaResolve } from 'import-meta-resolve'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const log = (msg) => process.stderr.write(`[persistent-renderer] ${msg}\n`)

/**
 * mermaid.jsのIIFEバンドルパスを解決する（mmdc L18と同じ方式）
 */
const resolveMermaidPath = () => {
  try {
    const mermaidUrl = importMetaResolve('mermaid', import.meta.url)
    // fileURLToPathでURLエンコード(%20等)を正しくデコードし、OS固有パスに変換
    const mermaidEntryPath = fileURLToPath(mermaidUrl)
    // mermaid/dist/mermaid.core.mjs → mermaid/dist/mermaid.min.js
    const dir = dirname(mermaidEntryPath)
    return join(dir, 'mermaid.min.js')
  } catch {
    // フォールバック: requireで解決
    const require = createRequire(import.meta.url)
    const mermaidPath = require.resolve('mermaid/dist/mermaid.min.js')
    return mermaidPath
  }
}

/**
 * 起動設定をコマンドライン引数からデコードする
 */
const parseStartupConfig = () => {
  const base64Config = process.argv[2]
  if (!base64Config) {
    return { puppeteerConfig: {}, mermaidConfig: {} }
  }
  try {
    const jsonStr = Buffer.from(base64Config, 'base64').toString('utf-8')
    return JSON.parse(jsonStr)
  } catch (err) {
    log(`起動設定のパースに失敗: ${err.message}`)
    return { puppeteerConfig: {}, mermaidConfig: {} }
  }
}

/**
 * stdinから1行読み取る
 */
const createLineReader = (stream) => {
  let buffer = ''
  const pending = []
  let closed = false

  stream.setEncoding('utf-8')

  stream.on('data', (chunk) => {
    buffer += chunk
    let newlineIdx
    while ((newlineIdx = buffer.indexOf('\n')) !== -1) {
      const line = buffer.substring(0, newlineIdx)
      buffer = buffer.substring(newlineIdx + 1)
      if (pending.length > 0) {
        const resolve = pending.shift()
        resolve(line)
      }
    }
  })

  stream.on('end', () => {
    closed = true
    // 残りのバッファがあれば最後の行として処理
    if (buffer.length > 0) {
      const line = buffer
      buffer = ''
      if (pending.length > 0) {
        const resolve = pending.shift()
        resolve(line)
      }
    }
    // 待機中のプロミスにnullを返す
    while (pending.length > 0) {
      const resolve = pending.shift()
      resolve(null)
    }
  })

  return () => {
    if (closed && buffer.length === 0) {
      return Promise.resolve(null)
    }
    // バッファに完全な行があるかチェック
    const newlineIdx = buffer.indexOf('\n')
    if (newlineIdx !== -1) {
      const line = buffer.substring(0, newlineIdx)
      buffer = buffer.substring(newlineIdx + 1)
      return Promise.resolve(line)
    }
    return new Promise((resolve) => {
      pending.push(resolve)
    })
  }
}

/**
 * レスポンスをstdoutにNDJSON形式で書き出す
 */
const sendResponse = (response) => {
  process.stdout.write(JSON.stringify(response) + '\n')
}

/**
 * Mermaidコードをレンダリングする（mmdc renderMermaid L247-280を参考）
 */
const renderMermaid = async (browser, mermaidIIFEPath, request, mermaidConfig) => {
  const { id, code, theme, css } = request
  let page = null

  try {
    page = await browser.newPage()

    // mermaid.jsを読み込み
    await page.addScriptTag({ path: mermaidIIFEPath })

    // mermaid.initialize + mermaid.render
    const svg = await page.evaluate(
      async (code, theme, mermaidConfig, css) => {
        // mermaid初期化（mmdc同様）
        const config = {
          ...mermaidConfig,
          theme: theme || 'default',
        }
        window.mermaid.initialize(config)

        // CSSがあればスタイルタグを追加
        if (css) {
          const style = document.createElement('style')
          style.textContent = css
          document.head.appendChild(style)
        }

        // レンダリング
        const { svg } = await window.mermaid.render('mermaid-svg', code)
        return svg
      },
      code,
      theme,
      mermaidConfig,
      css || ''
    )

    return { id, success: true, svg }
  } catch (err) {
    return { id, success: false, error: err.message || String(err) }
  } finally {
    if (page) {
      await page.close().catch(() => {})
    }
  }
}

/**
 * メインループ
 */
const main = async () => {
  const config = parseStartupConfig()
  const puppeteerConfig = config.puppeteerConfig || {}
  const mermaidConfig = config.mermaidConfig || {
    htmlLabels: false,
    flowchart: { htmlLabels: false },
    class: { htmlLabels: false },
  }

  // mermaid.jsのパスを解決
  let mermaidIIFEPath
  try {
    mermaidIIFEPath = resolveMermaidPath()
    log(`mermaid.jsのパスを解決: ${mermaidIIFEPath}`)
  } catch (err) {
    log(`mermaid.jsのパス解決に失敗: ${err.message}`)
    process.exit(1)
  }

  // ブラウザを起動（mmdc同様 headless: 'shell' を使用）
  let browser
  try {
    const launchOptions = {
      headless: 'shell',
      ...puppeteerConfig,
    }
    browser = await puppeteer.launch(launchOptions)
    log('ブラウザを起動しました')
  } catch (err) {
    log(`ブラウザの起動に失敗: ${err.message}`)
    process.exit(1)
  }

  // 親プロセス死亡を検知→ブラウザ閉じて終了
  process.stdin.on('end', async () => {
    log('stdin終了を検知、シャットダウンします')
    await browser.close().catch(() => {})
    process.exit(0)
  })

  // 準備完了を通知
  sendResponse({ ready: true })

  // NDJSONプロトコルでリクエストを処理
  const readLine = createLineReader(process.stdin)

  while (true) {
    const line = await readLine()
    if (line === null) {
      break
    }

    const trimmed = line.trim()
    if (!trimmed) {
      continue
    }

    let request
    try {
      request = JSON.parse(trimmed)
    } catch (err) {
      sendResponse({ id: null, success: false, error: `JSONパースエラー: ${err.message}` })
      continue
    }

    // シャットダウンコマンド
    if (request.command === 'shutdown') {
      log('シャットダウンコマンドを受信')
      await browser.close().catch(() => {})
      process.exit(0)
    }

    // レンダリングリクエスト
    const response = await renderMermaid(browser, mermaidIIFEPath, request, mermaidConfig)
    sendResponse(response)
  }

  // ループ終了時にブラウザを閉じる
  await browser.close().catch(() => {})
}

main().catch((err) => {
  log(`致命的エラー: ${err.message}`)
  process.exit(1)
})
