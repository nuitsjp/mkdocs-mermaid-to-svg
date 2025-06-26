現在、つねにすべてのmermaidを画像化しているために非常に動作が重たいです。
mkdocs serve時は画像化せず処理をパスするように修正してください。
まずは設計方針を説明してください。

# mkdocs serve判定方法

MkDocsで`mkdocs serve`が呼ばれたかどうかを起動直後に判断する方法はいくつかあります。

## 1. `sys.argv`を使用する方法（最もシンプル）

```python
import sys

def is_serve_command():
    return 'serve' in sys.argv

# プラグインの初期化時や設定読み込み時に使用
if is_serve_command():
    print("MkDocs serve mode detected")
```

## 2. プラグインの`on_config`フックで判定

```python
from mkdocs.plugins import BasePlugin
import sys

class YourPlugin(BasePlugin):
    def on_config(self, config):
        if 'serve' in sys.argv:
            # serve モードの処理
            self.is_serve_mode = True
        else:
            self.is_serve_mode = False
        return config
```

## 3. 環境変数を使用する方法

より確実な判定が必要な場合は、MkDocsの内部実装を確認することもできます：

```python
import os
import sys

def detect_serve_mode():
    # コマンドライン引数をチェック
    if 'serve' in sys.argv:
        return True

    # 開発サーバーの兆候をチェック
    if hasattr(sys, '_getframe'):
        frame = sys._getframe()
        while frame:
            if 'livereload' in str(frame.f_code.co_filename):
                return True
            frame = frame.f_back

    return False
```

## 4. MkDocsの設定オブジェクトを使用

```python
from mkdocs.plugins import BasePlugin

class YourPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.serve_mode = 'serve' in sys.argv

    def on_config(self, config):
        if self.serve_mode:
            # serve専用の設定
            config['dev_addr'] = config.get('dev_addr', '127.0.0.1:8000')
        return config
```

最も推奨される方法は**方法1**の`sys.argv`チェックです。これは：
- シンプルで確実
- MkDocsの内部実装に依存しない
- プラグインの初期化時点で判定可能

この方法で、`on_serve`フックが呼ばれるより前に serve モードかどうかを判定できます。
