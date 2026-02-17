import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import shutil
import json
import base64

# ページ設定
st.set_page_config(page_title="ファイブエムOS 可視化プロト", layout="wide")

# --- タイトルと説明 ---
st.title("🌌 ファイブエムOS 可視化プロト")
st.write("アンケート結果を『共鳴のエコー』として可視化します。")


# --- サイドバー：データ管理 ---
st.sidebar.header("🛠 データ管理")

# 1. CSVアップロード
uploaded_file = st.sidebar.file_uploader("新しいデータをアップロード (CSV)", type="csv")

if uploaded_file is not None:
    # Save the uploaded file
    with open("survey_data.csv", "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success("データが更新されました！アニメーションを再生成してください。")

# 2. アニメーション再生成ボタン
if st.sidebar.button("🎥 アニメーションを生成/更新"):
    with st.spinner('データを更新しています...'):
        try:
            # 直接importして実行（Streamlit Cloud環境でのライブラリ不整合回避）
            import gen_animation
            # もしgen_animation.pyが関数化されているなら実行、
            # そうでなければimportした時点でトップレベルのコードが実行されます。
            st.success("更新完了！")
            st.rerun() 
        except Exception as e:
            st.error(f"実行エラー: {e}")

# --- メイン表示エリア ---

# アニメーション表示
json_path = "animation_data.json"
bg_path = "universe_bg.png"

if os.path.exists(json_path):
    st.subheader("共鳴アニメーション (Real-time Render)")
    
    with open(json_path, "r", encoding='utf-8') as f:
        animation_data = json.load(f)
    
    bg_b64 = ""
    if os.path.exists(bg_path):
        with open(bg_path, "rb") as f:
            bg_b64 = base64.b64encode(f.read()).decode('utf-8')
            
    # 高解像度ディスプレイ(DPR)対応版 JavaScript/HTML
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ margin: 0; background-color: #020617; overflow: hidden; width: 100vw; height: 100vh; display: flex; justify-content: center; align-items: center; }}
        canvas {{ 
            display: block;
            image-rendering: -webkit-optimize-contrast; /* ブラウザ側のボケ防止 */
            image-rendering: crisp-edges;
        }}
    </style>
    </head>
    <body>
    <canvas id="canvas"></canvas>
    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        
        const data = {json.dumps(animation_data)};
        const bgData = "data:image/png;base64,{bg_b64}";
        
        const LIMIT = 500; 
        const RANGE = 1000;
        const DURATION_FRAMES = 4000; 
        const RIPPLE_CYCLE = 640; 
        
        let frame = 0;
        let startTime = null;
        let bgImage = new Image();
        let size = 1000;
        let offsetX = 0;
        let offsetY = 0;
        let dpr = window.devicePixelRatio || 1;

        function resize() {{
            dpr = window.devicePixelRatio || 1;
            // 物理ピクセルサイズに合わせる
            canvas.width = window.innerWidth * dpr;
            canvas.height = window.innerHeight * dpr;
            // CSSでの表示サイズ
            canvas.style.width = window.innerWidth + 'px';
            canvas.style.height = window.innerHeight + 'px';
            
            // 描画コンテキストをスケールアップ（これで文字がシャープになる）
            ctx.scale(dpr, dpr);
            
            size = Math.min(window.innerWidth, window.innerHeight);
            offsetX = (window.innerWidth - size) / 2;
            offset
