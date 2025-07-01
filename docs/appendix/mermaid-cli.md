

# **mermaid-cli 完全攻略: PNG生成パラメータの網羅的解説と動的な画像サイズ自動制御戦略**

## **序論: mermaid-cliの本質を理解する — 単なる画像コンバータではない**

本レポートは、mermaid-cli（コマンド名: mmdc）を用いてテキストベースのMermaid定義から高品質なPNG画像を生成するプロセスを完全にマスターすることを目指す、開発者およびテクニカルライター向けの決定版ガイドです。その目的は二つあります。第一に、mmdcが提供する全てのコマンドラインパラメータと設定オプションを網羅的かつ執拗に詳しく解説すること。第二に、小規模な図から大規模で複雑な図に至るまで、あらゆるケースで文字の判読性を損なうことなく、最適な画像サイズを自動的に決定するための高度で実践的な戦略を提示することです。

mermaid-cliの挙動を正確に理解する上で最も重要な点は、それが単純な画像変換ツールではないという事実です。その核心的な動作原理は、内部でPuppeteerのようなヘッドレスブラウザ（ユーザーインターフェースを持たないブラウザ）を起動し、そのブラウザ環境でMermaid.jsライブラリを実行し、ウェブページ上に描画された図を「スクリーンショット」としてキャプチャする、というものです 1。このアーキテクチャこそが、

\-w（幅）や-H（高さ）といったパラメータがなぜ直感とは異なる挙動を示すのか、その根本的な理由を説明します。これらのパラメータは最終的な画像サイズを直接指定するのではなく、内部ブラウザの表示領域（ビューポート）のサイズを制御しているに過ぎません。この基本原理の理解は、本レポート全体を貫く中心的な概念となります。

本レポートは、以下の構成でmermaid-cliの全貌を解き明かしていきます。まず第1部と第2部で、コマンドラインパラメータと設定ファイルという「静的な知識」を徹底的に解説します。次に、その知識を応用し、第3部で「動的な戦略」として、本レポートの核心的価値提案である画像サイズの自動制御アプローチを詳述します。最後に、第4部で具体的な実践例とトラブルシューティングを提供し、読者が直面しうる問題を解決するための具体的な手段を提示します。

## **第1部: mermaid-cli パラメータ大全 — コマンドラインからの制御**

このセクションでは、mmdcコマンドのコマンドラインインターフェースを徹底的に解剖し、PNG生成に利用可能な各パラメータの正確な役割、設定可能な値、そしてその挙動を明らかにします。

### **1.1. コマンドラインパラメータ一覧表**

mmdc \--helpコマンド 3 や公式ドキュメントから得られる情報、そして実際の使用例を基に、調査で確認できた全パラメータを網羅した包括的なリファレンステーブルを以下に示します。この表は、目的のパラメータを迅速に参照できるよう設計されています。

| パラメータ | 引数 | 説明 | デフォルト値 | 注釈・相互作用 |
| :---- | :---- | :---- | :---- | :---- |
| \-i, \--input | \<file\> | 入力となるMermaid定義ファイル（.mmd）またはMermaidコードブロックを含むMarkdownファイル（.md）。 | (必須) | \- を指定すると標準入力から読み込むことができます 3。 |
| \-o, \--output | \[file\] | 出力ファイルパス。拡張子（.png, .svg, .pdf）から出力形式が自動推測されます。 | inputファイルと同じディレクトリに出力 | 指定しない場合、SVG形式で標準出力に出力されることがあります。 |
| \-e, \--outputFormat | \[format\] | 出力形式を明示的に指定します (png, svg, pdf, md)。 | outputの拡張子から推測 | \-oでの推測を上書きしたい場合に使用します 5。 |
| \-t, \--theme | \[theme\] | 図のテーマを指定します。 | default | default, forest, dark, neutral などが利用可能です 3。 |
| \-w, \--width | \[width\] | ヘッドレスブラウザのビューポートの幅をピクセル単位で指定します。 | 800 | **注意:** これは最終的なPNG画像の幅を直接指定するものではありません。詳細は後述します。 |
| \-H, \--height | \[height\] | ヘッドレスブラウザのビューポートの高さをピクセル単位で指定します。 | 600 | **注意:** \-wと同様、ビューポートの高さを指定するものであり、画像サイズとは異なります。 |
| \-b, \--backgroundColor | \[color\] | 背景色を指定します。 | white | transparent, whiteのようなキーワードや\#F0F0F0のような16進数コードが使用可能です 1。 |
| \-c, \--configFile | \[file\] | Mermaidの動作を制御するJSON形式の設定ファイルを指定します。 | なし | フォントサイズや図固有の設定など、高度なカスタマイズに使用します 6。 |
| \-C, \--cssFile | \[file\] | 生成される図に適用するカスタムCSSファイルを指定します。 | なし | スタイルの微調整に使用しますが、テーマ自体の変更は-cが推奨されます 3。 |
| \-s, \--scale | \[scale\] | ブラウザのスケールファクタ（ズームレベル）を指定します。 | 1 | 高解像度化に影響しますが、-pオプションの方がより精密な制御が可能です 5。 |
| \-p, \--puppeteerConfigFile | \[file\] | Puppeteer（ヘッドレスブラウザ）の起動オプションをJSON形式で指定します。 | なし | 高解像度化やシステムブラウザの利用など、描画エンジン自体の制御に使用します 5。 |
| \-f, \--pdfFit |  | PDF出力時に、図がページに収まるようにスケーリングします。 | false | PDF出力時のみ有効なオプションです 5。 |
| \-q, \--quiet |  | ログ出力を抑制します。 | false | スクリプト内での実行時に有用です 5。 |
| \-I, \--svgId | \[id\] | SVG出力時に、\<svg\>要素に付与するIDを指定します。 | なし | SVGをHTMLに埋め込む際に使用します 5。 |
| \--icon-packs | \<icons...\> | 使用するアイコンパックを指定します（例: @iconify-json/logos）。 | なし | アイコンを利用する図（C4 डायグラムなど）で使用します 5。 |

### **1.2. 主要パラメータの詳細解説**

#### **1.2.1. 基本入出力 (-i, \-o, \-e)**

これらのパラメータはmmdcの最も基本的な操作を定義します。-iでMermaid定義が記述されたソースファイルを指定し、-oで成果物となる画像ファイルのパスを指定します 3。特筆すべきは、

\-i \-と指定することで、他のコマンドの出力をパイプで受け取り、動的に図を生成するワークフローを構築できる点です 3。出力形式は

\-oで指定したファイルの拡張子から自動的に推測されますが、-eオプションを使えば、例えば拡張子と異なる形式で強制的に出力することも可能です 5。

#### **1.2.2. 外観のカスタマイズ (-t, \-b)**

図の視覚的なスタイルは-t（テーマ）と-b（背景色）で簡単に変更できます。-tにはdefault、dark、forest、neutralといった定義済みのテーマが用意されており、コマンド一つで図全体のルックアンドフィールを切り替えられます 3。

\-bは背景色を指定するもので、transparentを指定すれば背景が透明なPNG画像を生成でき、他の画像やプレゼンテーションへの重ね合わせが容易になります 3。

whiteのようなキーワードや\#RRGGBB形式の16進数カラーコードも受け付けます 1。

#### **1.2.3. サイズとスケーリング (-w, \-H, \-s) — 最も誤解されやすいパラメータ群**

これらのパラメータはmermaid-cliの挙動を理解する上で最も重要かつ、最も混乱を招きやすい部分です。多くのユーザーがこれらのパラメータを最終的なPNG画像のピクセルサイズを直接指定するものだと期待しますが、それは正確ではありません。

前述の通り、mermaid-cliは内部でヘッドレスブラウザを動作させます。-wと-Hは、このブラウザの**ビューポート（表示領域）のサイズ**をピクセル単位で指定するためのものです 2。Mermaid.jsライブラリは、この与えられたビューポートの制約の中で、図のレイアウトを最適化しようと試みます。

このアーキテクチャから、以下の挙動が導かれます。

1. **図はビューポートを満たすとは限らない**: 小さな図を大きなビューポート（例: \-w 2000 \-H 2000）で描画しても、図が2000x2000ピクセルに引き伸ばされるわけではありません。図は本来のコンテンツサイズで描画され、周囲に大きな余白が生まれます。
2. **ビューポートはレイアウトに影響する**: 逆に、非常に複雑で大きな図を小さなビューポートで描画しようとすると、Mermaid.jsはコンテンツを無理に収めようとし、結果としてレイアウトが崩れたり、テキストが重なったりする可能性があります。
3. **サイズには上限が存在する可能性**: ユーザー報告によると、-wや-Hに非常に大きな値を設定しても、出力される画像のサイズがある一定の大きさ（例: 986x587ピクセル）で頭打ちになる現象が確認されています 9。これは、内部のPuppeteerや描画エンジンの設定に起因する制約の可能性があります。

複数のGitHub issueでは、ユーザーが-wや-Hを指定しても期待通りに画像サイズが変更されないという混乱が報告されており 9、開発者や他のユーザーからは、これらが「ウェブページのサイズ」であり、CLIは「ブラウザウィンドウ内で画像を生成する」ものであるという説明がなされています 2。したがって、これらのパラメータを扱う際は、「最終的な画像の寸法を指定している」のではなく、「図を描画するためのキャンバスの大きさを指定している」というメンタルモデルに切り替えることが不可欠です。

\-s, \--scaleオプションは、ブラウザのズームレベルに相当するスケールファクタを指定します 5。値を

2に設定すると、ビューポート内のすべての要素が2倍に拡大されてからキャプチャされるため、結果として高解像度の画像が得られます。しかし、これはレイアウト自体も拡大するため、フォントの絶対サイズの制御などを考えると、後述するpuppeteerConfigFile内のdeviceScaleFactorを用いる方がより洗練された制御方法と言えます。

#### **1.2.4. 高度な設定ファイル (-c, \-C, \-p)**

コマンドラインオプションだけでは実現できない、より詳細で高度なカスタマイズは、3つの設定ファイルを通じて行います。

* \-c, \--configFile: Mermaid.jsライブラリ自体の動作を定義するJSONファイルを指定します 6。フォントの種類やサイズ、各ダイアグラムタイプ（フローチャート、シーケンス図など）固有のレイアウトオプションなど、描画の根幹に関わる設定を行います。
* \-C, \--cssFile: 生成されたSVGに対して適用するカスタムCSSファイルを指定します 3。特定ノードの色や線のスタイルなど、最終的な見た目を微調整するために使用します。公式には、テーマ自体の変更は
  configFileで行うことが推奨されています 3。
* \-p, \--puppeteerConfigFile: ヘッドレスブラウザであるPuppeteerの起動オプションをJSON形式で指定します 5。高解像度PNGを生成するための
  deviceScaleFactorの設定や、システムにインストール済みのChromeブラウザを使用する設定など、描画エンジンそのものを制御するための最も強力な手段です。

これらの設定ファイルは階層的に機能し、連携させることでmermaid-cliの能力を最大限に引き出すことができます。次章では、これらのファイルの詳細な活用方法を解説します。

## **第2部: 設定ファイルによる階層的カスタマイズ**

mermaid-cliの真価は、コマンドラインオプションと3つの設定ファイルを組み合わせた階層的なカスタマイズにあります。これらの設定は、puppeteerConfigFile（描画環境の定義）、configFile（Mermaidコアライブラリの設定）、cssFile（最終的なスタイル調整）という順序で適用されます。この依存関係と優先順位を理解することが、高度な制御と効率的なトラブルシューティングの鍵となります。まず最も基盤となるブラウザ環境がpuppeteerConfigFileで定義され、その上で動作するMermaid.jsの挙動がconfigFileで制御され、最後に生成された図に対してcssFileで見た目の上書きが行われる、という流れです。

### **2.1. Mermaid設定ファイル (-c, \--configFile) の活用**

\-cまたは--configFileオプションで指定するJSONファイルは、Mermaid.jsライブラリの動作そのものを細かく制御するための心臓部です。

#### **テーマとフォントの制御**

themeVariablesオブジェクトを使用することで、図の基本的な外観を詳細にカスタマイズできます。これにより、企業のブランドガイドラインに沿った一貫性のあるデザインの図を生成することが可能になります。

**configFileにおける主要なthemeVariables**

| 変数名 | 説明 | デフォルト値 | 設定例 |
| :---- | :---- | :---- | :---- |
| fontSize | 図全体の基本フォントサイズをピクセル単位で指定します 11。 | 16px | "fontSize": "14px" |
| fontFamily | 図全体の基本フォントファミリーを指定します 11。 | trebuchet ms, verdana, arial | "fontFamily": "Arial, sans-serif" |
| primaryColor | ノードの背景色など、テーマの基本となる色を指定します。 | \#fff4dd | "primaryColor": "\#ECECFF" |
| primaryTextColor | primaryColorの背景に対するテキストの色を指定します。 | darkMode設定から計算 | "primaryTextColor": "\#333333" |
| primaryBorderColor | primaryColorを使用するノードの境界線の色を指定します。 | primaryColorから計算 | "primaryBorderColor": "\#9370DB" |
| lineColor | フローチャートの矢印など、図の線の色を指定します。 | backgroundから計算 | "lineColor": "\#333333" |
| background | 図の背景色。-bオプションと同様の役割を果たします。 | \#f4f4f4 | "background": "\#FFFFFF" |

#### **レイアウトの制御 (useMaxWidth)**

図のレイアウト、特にその幅の扱いに大きな影響を与えるのがuseMaxWidthオプションです 12。このブール値の設定は、図がビューポートの幅に対してどのように振る舞うかを決定します。

* "useMaxWidth": true（デフォルト）: 図は、与えられたビューポートの幅を最大限に活用しようとします。つまり、コンテナの幅に合わせてスケールします。
* "useMaxWidth": false: 図は、コンテンツ（ノードやテキストの量）に基づいて決定される絶対的なサイズで描画されます。ビューポートの幅には影響されにくくなります。

この設定は、特に第3部で解説する画像サイズの自動制御戦略において極めて重要な役割を果たします。GitHubのissueでも、幅が期待通りに適用されない問題の解決策としてこの設定の変更が提案されています 10。

以下は、フローチャートのフォントサイズとuseMaxWidthを設定するconfig.jsonの例です。

JSON

{
  "flowchart": {
    "useMaxWidth": false
  },
  "themeVariables": {
    "fontSize": "12px",
    "fontFamily": "Helvetica"
  }
}

### **2.2. カスタムCSSファイル (-C, \--cssFile) によるスタイルの注入**

configFileだけでは制御しきれない、より詳細なスタイルの調整には-Cまたは--cssFileオプションが役立ちます。これにより、標準的なCSSを注入して、生成されるSVGの要素を直接スタイリングできます 3。

例えば、特定のノードのパディングを増やしたり、特定のクラスを持つ矢印を破線にしたりといった、きめ細やかなデザイン調整が可能です。スタイリングには、以下のようなCSSセレクタが有効です。

* **図全体に適用**: .mermaid svg {... } 14
* **IDでSVGを特定**: svg\[id^="m"\] {... } （IDは動的に生成されるため注意が必要） 14
* **Mermaidのクラス定義を利用**: Mermaid定義内でclassDefを使ってクラスを定義し、CSSでそのクラスをスタイリングする方法が最も堅牢です。
  * Mermaid定義: graph TD; A--\>B; class A my-custom-style;
  * CSSファイル: .my-custom-style { stroke-width: 4px; fill: \#f9f; } 14

CSSのプロパティが期待通りに適用されない場合は、\!important宣言を使用することで強制的にスタイルを上書きできる場合がありますが、これは最終手段と考えるべきです 3。

### **2.3. Puppeteer設定ファイル (-p, \--puppeteerConfigFile) による描画エンジンの制御**

\-pまたは--puppeteerConfigFileオプションは、mermaid-cliのカスタマイズにおける最も強力なレイヤーであり、描画エンジンであるPuppeteerの起動オプションを直接制御します。このファイルの真価は、特に高解像度なPNG画像を生成する際に発揮されます。

#### **高解像度PNG生成の鍵 (deviceScaleFactor)**

高品質な出力を得るための最重要パラメータがdeviceScaleFactorです 17。これは、CSSピクセルと物理的なデバイスピクセルの比率を定義します。例えば、Retinaディスプレイでは1つのCSSピクセルが2x2の物理ピクセルで表示されるため、

deviceScaleFactorは2となります。

この値を2や3に設定すると、mermaid-cliは内部的に高解像度のディスプレイをエミュレートします。図のレイアウト（CSSピクセルベースのサイズ）はそのままに、キャプチャされる画像のピクセル密度が2倍、3倍になります。結果として、文字や線が非常に鮮明で、拡大してもぼやけない高品質なPNG画像を生成することができます。

以下に、puppeteerConfigFileで利用可能な主要なオプションを示します。

**puppeteerConfigFileの主要オプション**

| オプション | 型 | 説明 | 設定例 |
| :---- | :---- | :---- | :---- |
| executablePath | string | 使用するブラウザ（Chrome/Chromium）の実行可能ファイルへのパス。システムにインストール済みのブラウザを使用する場合に指定します 8。 | "executablePath": "/usr/bin/chromium-browser" |
| headless | boolean | ブラウザをヘッドレスモードで起動するかどうか。trueが通常です。 | "headless": true |
| defaultViewport | object | デフォルトのビューポート設定を上書きします。 | (下記参照) |
| defaultViewport.width | number | ビューポートの幅（ピクセル）。-wオプションより優先される可能性があります。 | "width": 1280 |
| defaultViewport.height | number | ビューポートの高さ（ピクセル）。-Hオプションより優先される可能性があります。 | "height": 720 |
| defaultViewport.deviceScaleFactor | number | デバイスのスケールファクタ。高解像度化の鍵となります 17。 | "deviceScaleFactor": 2 |

高解像度化（2倍）を実現するためのpuppeteer.jsonの具体的な記述例は以下の通りです。

JSON

{
  "defaultViewport": {
    "deviceScaleFactor": 2
  }
}

このファイルを-p puppeteer.jsonとしてmmdcコマンドに渡すことで、出力されるPNG画像の解像度を効果的に向上させることができます。

## **第3部: 文字が潰れないための画像サイズ自動制御戦略**

これまでのセクションで解説したパラメータと設定ファイルの知識を基に、本レポートの核心的な価値提案である「画像サイズの自動制御戦略」を提示します。この戦略の目的は、図の規模や複雑さに関わらず、常に文字が判読可能で、かつ不要な余白がない、最適な品質の画像を自動で生成することです。

### **3.1. 課題の再定義: なぜ固定サイズの指定では破綻するのか**

ドキュメンテーションの自動生成パイプラインにおいて、すべてのMermaid図に同じ固定サイズ（例: \-w 800 \-H 600）を適用するアプローチは、多くの場合破綻します。その理由は、図のコンテンツが動的であるためです。

* **小さな図の問題**: ノードが数個しかない単純なフローチャートに大きなビューポートを適用すると、図の周囲に広大な余白が生まれ、ドキュメントのレイアウトを不必要に占有してしまいます。
* **大きな図の問題**: 数十のエンティティとリレーションシップを持つ複雑なER図に小さなビューポートを適用すると、Mermaid.jsはコンテンツを無理やり収めようとし、ノードやテキストが重なり合って判読不能になるか、図の一部が切り取られてしまいます。

\--scale (-s) オプションも根本的な解決策にはなりません。このオプションは図全体を拡大・縮小するため、フォントサイズや線の太さといった要素の絶対的な制御が難しくなり、意図しないレンダリング結果を招くことがあります。求められているのは、図のコンテンツそのものにフィットするキャンバスサイズを動的に決定するメカニズムです。

### **3.2. 提案戦略: SVGを中間媒体とした二段階描画アプローチ**

この課題に対する最も堅牢かつ汎用的な解決策は、mermaid-cliを2回実行する「二段階描画（Two-Pass Rendering）」ワークフローを構築することです。このアプローチの鍵は、まず一度SVG形式で出力し、そのSVGから図の「真の寸法」を取得し、その寸法を使って完璧なサイズのビューポートで最終的なPNGを描画するという点にあります。

この手法は、SVGがベクター形式であり、レンダリングされた図の正確な幅と高さの情報が\<svg\>タグの属性として埋め込まれるという特性を利用します。実際に、この問題に直面したユーザーが、この回避策を考案し、コミュニティで共有しています 20。このアイデアを洗練させ、自動化されたスクリプトとして形式化することで、盤石なソリューションを構築できます。

#### **ワークフロー詳細**

1. **第一段階: 寸法特定のためのSVG一次描画**
   * まず、最終的なPNGではなく、一時的なSVGファイルとして図を出力します。この際、-wや-Hといったビューポートサイズを固定するオプションは指定しません。さらに、configFileで"useMaxWidth": falseを設定することが推奨されます。これにより、Mermaid.jsはビューポートの制約を受けず、コンテンツが必要とする本来のサイズでSVGを生成します。
   * **コマンド例:**
     Bash
     mmdc \-i input.mmd \-o temp.svg \-c config\_for\_svg.json

     ここでconfig\_for\_svg.jsonには{ "flowchart": { "useMaxWidth": false } }などが含まれます。
2. **第二段階: SVGからの寸法抽出**
   * 生成されたtemp.svgファイルをXMLパーサーや、grepとsedのような標準的なテキスト処理ツールを使って解析します。目的は、ルートの\<svg\>要素に記述されているwidth属性とheight属性の値（単位なしの数値）を抽出することです。
   * **シェルスクリプトでの抽出例:**
     Bash
     WIDTH=$(grep '\<svg' temp.svg | sed \-n 's/.\*width="\\(\[0-9.\]\*\\)".\*/\\1/p')
     HEIGHT=$(grep '\<svg' temp.svg | sed \-n 's/.\*height="\\(\[0-9.\]\*\\)".\*/\\1/p')

3. **第三段階: 最適ビューポートでのPNG最終描画**
   * 第二段階で抽出したwidthとheightの値を、mmdcの-wと-Hパラメータに設定して、再度コマンドを実行します。これにより、ビューポートのサイズが図のコンテンツに完璧にフィットします。
   * 同時に、高解像度化のために-pオプションでdeviceScaleFactorを設定したPuppeteer設定ファイルを指定します。これにより、「ジャストフィット」かつ「高解像度」という二つの要件を同時に満たすことができます。
   * **コマンド例:**
     Bash
     mmdc \-i input.mmd \-o output.png \-w "${WIDTH}" \-H "${HEIGHT}" \-p puppeteer\_high\_res.json

この二段階のアプローチにより、図の複雑さに関わらず、常に最適化された高品質なPNG画像を完全に自動で生成するパイプラインが完成します。

### **3.3. 戦略の比較と優位性**

提案した二段階描画アプローチの優位性を明確にするため、他の手法と比較します。

| 戦略 | 動作原理 | 利点 | 欠点 | 最適な用途 |
| :---- | :---- | :---- | :---- | :---- |
| **固定ビューポート** | \-wと-Hで常に同じサイズのビューポートを指定する。 | シンプルで実装が容易。 | 図のサイズによって余白が過大になるか、コンテンツが収まらない。品質が安定しない。 | すべての図のサイズがほぼ同じであることが保証されている稀なケース。 |
| **スケールオプション** | \-sでビューポート全体を拡大・縮小する。 | ある程度の高解像度化が可能。 | レイアウト自体がスケールするため、フォントや線の太さの絶対的な制御が難しい。根本的なサイズ問題は解決しない。 | 手動で素早く解像度を調整したい場合の一時的な解決策。 |
| **二段階描画 (SVG経由)** | 一度SVGで描画して寸法を取得し、その寸法でPNGを再描画する。 | **コンテンツにジャストフィット**する。不要な余白がない。**常に最適なサイズ**を保証。deviceScaleFactorとの組み合わせで**高解像度化も両立**できる。 | 実装がやや複雑になる（スクリプトが必要）。描画プロセスが2回実行されるため、処理時間が伸びる。 | **品質と一貫性が最優先される、ドキュメンテーションの自動生成パイプライン。** |

この比較から明らかなように、二段階描画戦略は、初期設定の複雑さを補って余りあるほどの品質と安定性をもたらします。これは、プロフェッショナルなドキュメンテーション環境において、手動調整の手間を完全に排除するための最も優れた投資と言えます。

## **第4部: 実践的用例とトラブルシューティング**

この最終セクションでは、第3部で提案した戦略を具体的なコードに落とし込み、読者が直面しうる一般的な問題とその解決策を提供します。

### **4.1. 総合的な実践例（シェルスクリプト）**

以下に、第3部で詳述した「二段階描画アプローチ」を実装した、コピー＆ペーストしてすぐに利用可能なシェルスクリプトの完全なサンプルを示します。このスクリプトは、入力ファイル名を第一引数として受け取り、一連のプロセスを自動で実行します。

#### **準備する設定ファイル**

スクリプトを実行する前に、以下の3つのファイルを同じディレクトリに用意します。

1. **generate-mermaid-png.sh** (実行権限を付与: chmod \+x generate-mermaid-png.sh)
   Bash
   \#\!/bin/bash

   \# スクリプトの使用法:./generate-mermaid-png.sh \<input\_file.mmd\>

   set \-e \# エラーが発生したらスクリプトを終了

   INPUT\_FILE="$1"
   if; then
     echo "エラー: 入力ファイルが指定されていません。"
     echo "使用法: $0 \<input\_file.mmd\>"
     exit 1
   fi

   BASE\_NAME=$(basename "${INPUT\_FILE}".mmd)
   OUTPUT\_PNG="${BASE\_NAME}.png"
   TEMP\_SVG="temp\_${BASE\_NAME}.svg"

   echo "ステップ1: 寸法特定のための一時SVGを生成中..."
   npx \-p @mermaid-js/mermaid-cli mmdc \-i "${INPUT\_FILE}" \-o "${TEMP\_SVG}" \-c config\_for\_svg.json

   echo "ステップ2: SVGから幅と高さを抽出中..."
   \# SVGからwidthとheightを抽出（小数点以下を切り捨て）
   WIDTH=$(grep '\<svg' "${TEMP\_SVG}" | sed \-n 's/.\*width="\\(\[0-9.\]\*\\)".\*/\\1/p' | cut \-d'.' \-f1)
   HEIGHT=$(grep '\<svg' "${TEMP\_SVG}" | sed \-n 's/.\*height="\\(\[0-9.\]\*\\)".\*/\\1/p' | cut \-d'.' \-f1)

   if ||; then
       echo "エラー: SVGから寸法の抽出に失敗しました。"
       rm \-f "${TEMP\_SVG}"
       exit 1
   fi
   echo "  \-\> 抽出された寸法: Width=${WIDTH}, Height=${HEIGHT}"

   echo "ステップ3: 最適なビューポートで高解像度PNGを生成中..."
   npx \-p @mermaid-js/mermaid-cli mmdc \\
     \-i "${INPUT\_FILE}" \\
     \-o "${OUTPUT\_PNG}" \\
     \-w "${WIDTH}" \\
     \-H "${HEIGHT}" \\
     \-p puppeteer\_high\_res.json

   echo "クリーンアップ: 一時SVGファイルを削除中..."
   rm \-f "${TEMP\_SVG}"

   echo "完了！ ${OUTPUT\_PNG} が生成されました。"

2. **config\_for\_svg.json** (SVG生成用設定ファイル)
   JSON
   {
     "flowchart": {
       "useMaxWidth": false
     },
     "sequence": {
       "useMaxWidth": false
     }
   }

3. **puppeteer\_high\_res.json** (高解像度PNG生成用設定ファイル)
   JSON
   {
     "defaultViewport": {
       "deviceScaleFactor": 2
     }
   }

#### **実行方法**

Mermaid定義ファイル（例: my\_diagram.mmd）を用意し、ターミナルで以下のコマンドを実行します。

Bash

./generate-mermaid-png.sh my\_diagram.mmd

これにより、my\_diagram.pngという名前で、コンテンツに最適化され、かつ2倍の解像度を持つ高品質な画像が生成されます。

### **4.2. よくある問題と解決策 (FAQ)**

**問題: \-w/-H を指定しても画像サイズが変わらない、または上限があるように見える。**

* **原因**: これはmermaid-cliの仕様です。これらのパラメータは最終的な画像サイズではなく、内部ブラウザのビューポートサイズを指定するものです。図のコンテンツが小さい場合、ビューポートいっぱいに広がることはありません。また、内部的な制約によりサイズに上限が設けられている可能性があります 2。
* **解決策**: 第3部で提案した「二段階描画アプローチ」を採用してください。これにより、コンテンツに基づいた正確なサイズで画像を生成できます。

**問題: テキストがノードからはみ出す、または途中で切れる。**

* **原因**: これは多くの場合、Mermaid.jsがテキストの寸法を計算する際のレイアウト計算の問題や、カスタムフォントの読み込みタイミングに起因します 21。
* **解決策**: 以下の複数のアプローチを試してください。
  1. **フォントサイズの調整**: \-cで指定するconfigFile内で、themeVariablesのfontSizeを少し小さく設定します。
  2. **改行の挿入**: ノード内のテキストに明示的に\<br/\>タグを挿入して高さを確保します。これにより、テキストが収まるスペースを強制的に作ることができます 22。
  3. **パディングの調整**: \-Cで指定するcssFileを使い、classDefで定義したカスタムクラスに対してpaddingを追加して、ノードの内側の余白を広げます 23。

**問題: \-s, \--scaleオプションが期待通りに機能しない、または画像がぼやける。**

* **原因**: scaleオプションはビューポート全体を拡大するため、ベクターデータではないフォントなどがぼやける原因になり得ます。また、puppeteerConfigFileの設定と競合する可能性も考えられます 24。
* **解決策**: \-sオプションの使用は避け、代わりに-pオプションでpuppeteerConfigFileを指定し、その中でdeviceScaleFactorを2や3に設定する方法を強く推奨します。この方がはるかに高品質で安定した結果が得られます。

**問題: Linux環境で実行するとサンドボックスに関するエラーが発生する。**

* **原因**: mermaid-cliが内部で使用するPuppeteerは、セキュリティのためにChromiumのサンドボックス機能を要求します。Dockerコンテナ内など、一部のCI/CD環境ではこのサンドボックスを有効にするための権限や依存関係が不足していることがあります 25。
* **解決策**:
  1. **Dockerコンテナの使用**: 公式またはコミュニティが提供するmermaid-cliのDockerイメージを使用するのが最も安全で確実な方法です 3。
  2. **サンドボックスの無効化（非推奨）**: puppeteerConfigFileに"args": \["--no-sandbox", "--disable-setuid-sandbox"\]を追加することで、サンドボックスを無効化してエラーを回避できます。ただし、これはセキュリティリスクを伴うため、信頼できないMermaidソースを処理する場合は絶対に避けるべきです。

## **結論: mermaid-cliをマスターするための三つの鍵**

本レポートでは、mermaid-cli (mmdc) のPNG生成機能について、そのパラメータから高度なカスタマイズ、そして実用的な自動化戦略に至るまで、徹底的な解説を行いました。この詳細な分析を通じて、mermaid-cliをプロフェッショナルレベルで使いこなすための三つの鍵が明らかになりました。

1. **メンタルモデルの転換**: mermaid-cliを単純な画像コンバータとして捉えるのではなく、\*\*「ヘッドレスブラウザの自動操作ツール」\*\*として理解することが第一の鍵です。この認識を持つことで、-wや-Hといったパラメータがなぜビューポートに作用するのか、そしてなぜ最終的な画像サイズと直接一致しないのかという、ツールの根本的な挙動を正確に把握できます。
2. **階層的設定の活用**: 第二の鍵は、**コマンドライン、configFile、cssFile、puppeteerConfigFileという4つの設定レイヤーの役割分担を理解し、目的に応じて適切に使い分ける**ことです。描画エンジン自体の制御（高解像度化など）はpuppeteerConfigFileで、Mermaidライブラリのコアな挙動（テーマやフォント）はconfigFileで、そして最終的な見た目の微調整はcssFileで行う。この階層構造をマスターすることで、あらゆるカスタマイズ要求に体系的に対応できます。
3. **二段階描画戦略の導入**: そして最も重要な第三の鍵が、**品質とサイズの両方を自動制御するための究極のソリューションとして、SVGを中間媒体とする「二段階描画戦略」を導入する**ことです。このアプローチは、図の複雑さに依存せず、常にコンテンツにジャストフィットした、不要な余白のない高品質な画像を生成する唯一の確実な方法です。実装には一手間かかりますが、ドキュメンテーションの自動化パイプラインに組み込むことで、手作業による調整という非効率なプロセスから開発者を完全に解放します。

これら三つの鍵をマスターすることにより、開発者やテクニカルライターは、mermaid-cliを単なるツールとして使うのではなく、ドキュメンテーションの品質と生産性を飛躍的に向上させるための強力な資産として活用できるようになるでしょう。

#### **引用文献**

1. Mermaid diagrams \- presenterm documentation, 6月 30, 2025にアクセス、 [https://mfontanini.github.io/presenterm/features/code/mermaid.html](https://mfontanini.github.io/presenterm/features/code/mermaid.html)
2. width / height options do not alter the size of the generated PNG ..., 6月 30, 2025にアクセス、 [https://github.com/mermaidjs/mermaid.cli/issues/3](https://github.com/mermaidjs/mermaid.cli/issues/3)
3. mermaid-js/mermaid-cli: Command line tool for the Mermaid library \- GitHub, 6月 30, 2025にアクセス、 [https://github.com/mermaid-js/mermaid-cli](https://github.com/mermaid-js/mermaid-cli)
4. mermaid-cli \- Codesandbox, 6月 30, 2025にアクセス、 [http://codesandbox.io/p/github/elicharlese/mermaid-cli](http://codesandbox.io/p/github/elicharlese/mermaid-cli)
5. seigok/mermaid-cli-python \- GitHub, 6月 30, 2025にアクセス、 [https://github.com/seigok/mermaid-cli-python](https://github.com/seigok/mermaid-cli-python)
6. Make-ing Mermaid, 6月 30, 2025にアクセス、 [https://serialized.net/2019/08/mermaid/](https://serialized.net/2019/08/mermaid/)
7. Set mermaid.initialize property in Mermaid CLI \- Stack Overflow, 6月 30, 2025にアクセス、 [https://stackoverflow.com/questions/52094200/set-mermaid-initialize-property-in-mermaid-cli](https://stackoverflow.com/questions/52094200/set-mermaid-initialize-property-in-mermaid-cli)
8. mermaid-cli/docs/already-installed-chromium.md at master \- GitHub, 6月 30, 2025にアクセス、 [https://github.com/mermaid-js/mermaid-cli/blob/master/docs/already-installed-chromium.md](https://github.com/mermaid-js/mermaid-cli/blob/master/docs/already-installed-chromium.md)
9. Width argument not taken into account · Issue \#73 · mermaid-js ..., 6月 30, 2025にアクセス、 [https://github.com/mermaid-js/mermaid-cli/issues/73](https://github.com/mermaid-js/mermaid-cli/issues/73)
10. Question \- How to change flowchart width? · Issue \#61 · mermaidjs/mermaid.cli \- GitHub, 6月 30, 2025にアクセス、 [https://github.com/mermaidjs/mermaid.cli/issues/61](https://github.com/mermaidjs/mermaid.cli/issues/61)
11. Theme Configuration | Mermaid, 6月 30, 2025にアクセス、 [https://mermaid.js.org/config/theming.html](https://mermaid.js.org/config/theming.html)
12. Base Diagram Config Schema \- Mermaid, 6月 30, 2025にアクセス、 [https://mermaid.js.org/config/schema-docs/config-defs-base-diagram-config.html](https://mermaid.js.org/config/schema-docs/config-defs-base-diagram-config.html)
13. Directives \- Mermaid, 6月 30, 2025にアクセス、 [https://mermaid.js.org/config/directives](https://mermaid.js.org/config/directives)
14. Let the user decide the size and alignment of mermaid diagrams ..., 6月 30, 2025にアクセス、 [https://forum.obsidian.md/t/let-the-user-decide-the-size-and-alignment-of-mermaid-diagrams/7019](https://forum.obsidian.md/t/let-the-user-decide-the-size-and-alignment-of-mermaid-diagrams/7019)
15. Mermaid graph size \- Support \- Joplin Forum, 6月 30, 2025にアクセス、 [https://discourse.joplinapp.org/t/mermaid-graph-size/7571](https://discourse.joplinapp.org/t/mermaid-graph-size/7571)
16. Change size of Mermaid.render generated SVG? \- Stack Overflow, 6月 30, 2025にアクセス、 [https://stackoverflow.com/questions/69094109/change-size-of-mermaid-render-generated-svg](https://stackoverflow.com/questions/69094109/change-size-of-mermaid-render-generated-svg)
17. Viewport interface \- Puppeteer, 6月 30, 2025にアクセス、 [https://pptr.dev/api/puppeteer.viewport](https://pptr.dev/api/puppeteer.viewport)
18. How do I update the viewport size or device scale factor in Puppeteer-Sharp?, 6月 30, 2025にアクセス、 [https://webscraping.ai/faq/puppeteer-sharp/how-do-i-update-the-viewport-size-or-device-scale-factor-in-puppeteer-sharp](https://webscraping.ai/faq/puppeteer-sharp/how-do-i-update-the-viewport-size-or-device-scale-factor-in-puppeteer-sharp)
19. Viewport in Puppeteer: How to Manipulate Default Size \- Webshare, 6月 30, 2025にアクセス、 [https://www.webshare.io/academy-article/puppeteer-viewport](https://www.webshare.io/academy-article/puppeteer-viewport)
20. Automatically determine output width · Issue \#816 · mermaid-js/mermaid-cli \- GitHub, 6月 30, 2025にアクセス、 [https://github.com/mermaid-js/mermaid-cli/issues/816](https://github.com/mermaid-js/mermaid-cli/issues/816)
21. API-Usage \- Mermaid Chart, 6月 30, 2025にアクセス、 [https://docs.mermaidchart.com/mermaid-oss/config/usage.html](https://docs.mermaidchart.com/mermaid-oss/config/usage.html)
22. Truncated text and custom font families · Issue \#1540 · mermaid-js/mermaid \- GitHub, 6月 30, 2025にアクセス、 [https://github.com/mermaid-js/mermaid/issues/1540](https://github.com/mermaid-js/mermaid/issues/1540)
23. How to increase node size in MermaidJS? \- flowchart \- Stack Overflow, 6月 30, 2025にアクセス、 [https://stackoverflow.com/questions/77137142/how-to-increase-node-size-in-mermaidjs](https://stackoverflow.com/questions/77137142/how-to-increase-node-size-in-mermaidjs)
24. Empty diagram generation. \#724 \- mermaid-js/mermaid-cli \- GitHub, 6月 30, 2025にアクセス、 [https://github.com/mermaid-js/mermaid-cli/issues/724](https://github.com/mermaid-js/mermaid-cli/issues/724)
25. @mermaid-js/mermaid-cli \- npm, 6月 30, 2025にアクセス、 [https://www.npmjs.com/package/@mermaid-js/mermaid-cli](https://www.npmjs.com/package/@mermaid-js/mermaid-cli)
