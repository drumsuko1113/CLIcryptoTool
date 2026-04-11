# ETH Trading Terminal - プロジェクト規約

## プロジェクト概要
Windows ターミナルで動作するETHトレード支援CLIアプリ（Python）。
自動売買なし、情報提供のみ。表示言語は日本語。

## 技術スタック
- Python 3.10+
- データソース: Binance公開API（価格）、RSS（ニュース）
- 追加のAPI課金・登録不要

## ブランチ戦略
- `main` — 安定版リリースブランチ
- `develop` — 統合ブランチ（feature ブランチはここにマージ）
- `feature/*` — 機能開発ブランチ（develop から分岐、develop へPR経由でマージ）
- `fix/*` — バグ修正ブランチ（develop から分岐、develop へPR経由でマージ）

## 開発フロー
1. feature ブランチを develop から作成
2. TDD で実装（テストを先に書く → 実装 → リファクタリング）
3. リファクタリング完了後 push
4. PR を作成して develop にマージ（PR経由必須）
5. 全機能完了後、develop → main へPR経由でマージ

## 品質ゲート（GitHub Actions CI/CD）
- pytest による自動テスト
- flake8 によるリント
- PR マージ前に CI パス必須

## 修正フロー
- 動作確認で問題が見つかった場合は `fix/*` ブランチを切って修正
- 修正もTDDで行い、PR経由でマージ
- この反復でゴール（全機能正常動作）まで繰り返す

## コマンド一覧
| コマンド | 説明 |
|---------|------|
| /price | 現在価格表示（ETH/JPY・ETH/USD） |
| /chart | ターミナル内ローソク足チャート |
| /news | RSS でニュース取得 |
| /iran | イラン関連ニュースフィルタ |
| /analysis | ルールベース自動分析（日本語） |
| /position | ポジション損益確認 |
| /alert <価格> | アラート設定 |
| /ask | claude.ai連携プロンプト生成 |

## テスト実行
```bash
pytest tests/ -v
```

## リント実行
```bash
flake8 src/ tests/
```

## アプリ起動
```bash
python -m src.main
```

## ディレクトリ構成
```
ETH CLI app/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── .github/workflows/ci.yml
├── src/
│   ├── __init__.py
│   ├── main.py          # エントリポイント・REPL
│   ├── price.py         # 価格取得（Binance API）
│   ├── chart.py         # チャート描画・テクニカル指標
│   ├── alert.py         # アラート管理
│   ├── position.py      # ポジション管理
│   ├── news.py          # RSS ニュース取得
│   ├── analysis.py      # ルールベース分析
│   └── ask.py           # claude.ai連携
├── tests/
│   ├── __init__.py
│   ├── test_price.py
│   ├── test_chart.py
│   ├── test_alert.py
│   ├── test_position.py
│   ├── test_news.py
│   ├── test_analysis.py
│   └── test_ask.py
└── config/
    └── position.json    # ポジション設定ファイル
```
