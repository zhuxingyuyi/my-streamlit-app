import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import json
import base64

# ページ設定
st.set_page_config(page_title="ファイブエムOS 可視化プロト", layout="wide")

# --- タイトルと説明 ---
st.title("🌌 ファイブエムOS 可視化プロト")
st.write("アンケート結果を『共鳴のエコー』として可視化します。")

# --- サイドバー：データ管理 ---
st.sidebar.header("🛠 データ管理")

# --- フィルター機能の修正（色コードをカテゴリー名に変換） ---
selected_colors = []
json_path = "animation_data.json"

if os.path.exists(json_path):
    with open(json_path, "r", encoding='utf-8') as f:
        tmp_data = json.load(f)
    
    # 色とカテゴリー名の対応表（辞書）を作成
    # gen_animation.pyの仕様に基づき、ノードから色と名前のペアを抽出
    color_to_label = {}
    for node in tmp_data['nodes']:
        color = node.get('color')
        # animation_data.jsonに元のカテゴリー名が含まれていない場合、
        # ここでは便宜上、色をキーにして表示名を管理します。
        # もしデータ側に 'category' 等があればそれを使えますが、
        # 現状は「どの色がどのグループか」を自動判別します。
        if color not in color_to_label:
            # カテゴリー名が不明な場合、ユーザーが判別しやすいようラベル化
            color_to_label[color] = color 

    # もしCSVがあれば、Q4_Switchの値と色の対応をより正確に紐付け
    if os.path.exists("survey_data.csv"):
        df_sample = pd.read_csv("survey_data.csv")
        if 'Q4_Switch' in df_sample.columns:
            categories = df_sample['Q4_Switch'].unique()
            # カテゴリー名を表示用、色を内部値として保持するためのリスト
            label_to_color = {}
            # gen_animation.pyのロジックと同じ順序で色を割り当てるか、
            # animation_data.jsonの各ノードのnameから逆引きして紐付け
            for node in tmp_data['nodes']:
                for cat in categories:
                    # ここでは簡易的に「特定のカテゴリーに属するノードの色」を学習
                    # ※実際のgen_animation.pyの色割り当てロジックに依存します
                    label_to_color[cat] = node['color'] 
            
            # 修正：より確実に「カテゴリー名」で選択させる
            st.sidebar.subheader("🎯 カテゴリー表示")
            selected_labels = st.sidebar.multiselect(
                "表示するカテゴリーを選択",
                options=list(label_to_color.keys()),
                default=[]
            )
            # 選択されたカテゴリー名に対応する「色コード」のリストに変換
            selected_colors = [label_to_color[lbl] for lbl in selected_labels]

st.sidebar.divider()

# --- 以下、アップロードと描画ロジック ---
uploaded_file = st.sidebar.file_uploader("CSVアップロード", type="csv")
if uploaded_file:
    with open("survey_data.csv", "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success("更新完了！再生成してください。")

if st.sidebar.button("🎥 アニメーションを生成/更新"):
    with st.spinner('更新中...'):
        try:
            import gen_animation
            st.success("完了！")
            st.rerun() 
        except Exception as e:
            st.error(f"エラー: {e}")

if os.path.exists(json_path):
    with open(json_path, "r", encoding='utf-8') as f:
        animation_data = json.load(f)
    
    bg_b64 = ""
    if os.path.exists("universe_bg.png"):
        with open("universe_bg.png", "rb") as f:
            bg_b64 = base64.b64encode(f.read()).decode('utf-8')
            
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ margin: 0; background-color: #020617; overflow: hidden; width: 100vw; height: 100vh; display: flex; justify-content: center; align-items: center; }}
        canvas {{ display: block; image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges; }}
    </style>
    </head>
    <body>
    <canvas id="canvas"></canvas>
    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const data = {json.dumps(animation_data)};
        const bgData = "data:image/png;base64,{bg_b64}";
        const activeColors = {json.dumps(selected_colors)};
        
        const LIMIT = 500; const RANGE = 1000;
        const DURATION_FRAMES = 4000; const RIPPLE_CYCLE = 640; 
        let frame = 0; let startTime = null; let bgImage = new Image();
        let size, offsetX, offsetY;

        function resize() {{
            const dpr = window.devicePixelRatio || 1;
            canvas.width = window.innerWidth * dpr;
            canvas.height = window.innerHeight * dpr;
            canvas.style.width = window.innerWidth + 'px';
            canvas.style.height = window.innerHeight + 'px';
            ctx.scale(dpr, dpr);
            size = Math.min(window.innerWidth, window.innerHeight);
            offsetX = (window.innerWidth - size) / 2;
            offsetY = (window.innerHeight - size) / 2;
        }}
        window.addEventListener('resize', resize);
        resize();
        
        bgImage.onload = () => {{ requestAnimationFrame(loop); }};
        bgImage.src = bgData;
        
        const mapX = (x) => offsetX + ((x + LIMIT) / RANGE) * size;
        const mapY = (y) => offsetY + size * (1 - (y + LIMIT) / RANGE);

        function loop(timestamp) {{
            if (!startTime) startTime = timestamp;
            frame = Math.floor((timestamp - startTime) / 50);
            ctx.imageSmoothingEnabled = false; 
            
            const bgRatio = bgImage.width / bgImage.height;
            const canvasRatio = window.innerWidth / window.innerHeight;
            let dw, dh, dx, dy;
            if (canvasRatio > bgRatio) {{
                dw = window.innerWidth; dh = window.innerWidth / bgRatio;
                dx = 0; dy = (window.innerHeight - dh) / 2;
            }} else {{
                dh = window.innerHeight; dw = window.innerHeight * bgRatio;
                dx = (window.innerWidth - dw) / 2; dy = 0;
            }}
            ctx.drawImage(bgImage, dx, dy, dw, dh);
            
            data.lines.forEach(l => {{
                if (frame >= l.delay) {{
                    const n1 = data.nodes[l.source]; const n2 = data.nodes[l.target];
                    const isVisible = activeColors.length === 0 || activeColors.includes(n1.color) || activeColors.includes(n2.color);
                    if (isVisible) {{
                        const alphaBase = Math.min(0.4, (frame - l.delay) / 320);
                        ctx.beginPath();
                        ctx.moveTo(mapX(n1.x), mapY(n1.y));
                        ctx.lineTo(mapX(n2.x), mapY(n2.y));
                        ctx.strokeStyle = "rgba(255, 255, 255, " + alphaBase + ")";
                        ctx.lineWidth = 1.0; ctx.stroke();
                    }}
                }}
            }});
            
            data.nodes.forEach(n => {{
                if (frame >= n.delay) {{
                    const isSelected = activeColors.length === 0 || activeColors.includes(n.color);
                    const baseAlpha = Math.min(1.0, (frame - n.delay) / 120);
                    const alpha = isSelected ? baseAlpha : baseAlpha * 0.1;
                    const x = mapX(n.x); const y = mapY(n.y);
                    
                    if (isSelected) {{
                        const relFrame = (frame - n.delay) % RIPPLE_CYCLE;
                        const progress = relFrame / RIPPLE_CYCLE;
                        const rPx = (progress * (n.score * 4.5) / RANGE) * size;
                        ctx.beginPath();
                        ctx.arc(x, y, rPx, 0, Math.PI * 2);
                        ctx.strokeStyle = n.color;
                        ctx.lineWidth = 3.0; 
                        ctx.globalAlpha = Math.max(0, 1.2 * (1 - progress)); 
                        ctx.stroke();
                        ctx.globalAlpha = 1.0;
                    }}

                    ctx.beginPath();
                    ctx.arc(x, y, (80/RANGE * size / 2), 0, Math.PI*2);
                    ctx.fillStyle = "rgba(255, 255, 255, " + (alpha * 0.075) + ")";
                    ctx.fill();
                    ctx.beginPath();
                    ctx.arc(x, y, (40/RANGE * size / 2 * 0.7), 0, Math.PI*2);
                    ctx.fillStyle = "rgba(255, 255, 255, " + (alpha * 0.2) + ")";
                    ctx.fill();
                    ctx.beginPath();
                    ctx.arc(x, y, 3, 0, Math.PI*2); 
                    ctx.fillStyle = "rgba(255, 255, 255, " + (alpha * 0.9) + ")";
                    ctx.fill();
                    ctx.fillStyle = "rgba(255, 255, 255, " + (alpha * 0.7) + ")";
                    ctx.font = 'bold 9px sans-serif'; 
                    ctx.fillText(n.name, x + 8, y - 5);
                }}
            }});
            if (frame < DURATION_FRAMES) requestAnimationFrame(loop);
        }}
    </script>
    </body>
    </html>
    """
    components.html(html_code, height=750, scrolling=False)

# --- 静止画エリア (変更なし) ---
static_path = "static_network_glow.png"
if os.path.exists(static_path):
    st.divider()
    st.subheader("静止画 (Motionless) - Zoomable")
    with open(static_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    st.components.v1.html(f'<img src="data:image/png;base64,{img_b64}" style="width:100%; max-width:750px;">', height=750)
