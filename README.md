# excel-input-sample-app-poc

## アプリ概要
本アプリは、ローカル環境で動作する簡易入力用 PoC です。
ブラウザから入力したデータを保存し、確定時に Excel にまとめて出力する流れを体験できるようにしています。

本プロジェクトは、教育や検証用途を目的とし、認証や権限管理などの本番向け機能は実装しません。

## 主な機能
- 入力フォームの表示
- 氏名から社員番号の自動連携
- 入力データの JSON 保存
- 確定時の Excel 生成
- 既存 Excel のバックアップ保存
- ローカル環境での簡易動作

## 使用技術
- Python
- FastAPI
- HTML
- JavaScript
- openpyxl

## 前提条件
- Windows のローカル環境
- Python 3.10 以上を利用可能であること
- ブラウザでアクセスできること

## ディレクトリ構成
```text
excel-input-sample-app-poc/
├─ app.py
├─ routes.py
├─ roster.json
├─ requirements.txt
├─ README.md
├─ docs/
│  ├─ 01.requirements.md
│  ├─ 02.basic_design.md
│  └─ 03.detailed_design.md
├─ services/
│  ├─ storage_service.py
│  ├─ roster_service.py
│  └─ excel_service.py
├─ template/
│  └─ template.xlsx
├─ templates/
│  └─ index.html
├─ static/
│  ├─ css/
│  │  └─ style.css
│  └─ js/
│     └─ app.js
└─ tests/
   └─ test_app.py
```

`data/`、`backup/`、`template/template.xlsx` は、アプリ起動時に存在しなければ自動生成されます。
確定処理で生成される Excel ファイルは、プロジェクトのルートディレクトリに `YYYY-MM-DD.xlsx` の名前で保存されます。

## 実行手順

1. 仮想環境を作成する
   ```powershell
   python -m venv .venv
   ```

2. 仮想環境を有効化する
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. 依存パッケージをインストールする
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. テストを実行する
   ```powershell
   python -m unittest discover -s tests -p "test_*.py"
   ```

5. 開発サーバーを起動する
   ```powershell
   uvicorn app:app --reload
   ```

6. ブラウザでアクセスする
   ```text
   http://127.0.0.1:8000
   ```

## 補足
- 本プロジェクトはローカル環境の PoC を想定する
- 認証や権限管理は実装しない
- 入力したデータは `data/YYYY-MM-DD.json` に JSON 形式で保存する
- 同じ日付・社員のデータを保存すると、既存レコードを最新の内容で置き換える
- 確定時に `template/template.xlsx` を元に Excel を生成し、既存の出力ファイルは `backup/` に退避する
- 確定後も JSON の一時保存データは削除せず、再出力に利用する
- 本番運用向けの高度な機能は含めない
