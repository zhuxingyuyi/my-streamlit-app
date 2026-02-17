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

uploaded_file = st.sidebar.file_uploader("新しいデータをアップロード (CSV)", type="csv")
if uploaded_file is not None:
    with open("survey_data.csv", "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success("データが更新されました！アニメーションを再生成してください。")

if st.sidebar.button("🎥 アニメーションを生成/更新"):
    with st.spinner('データを更新しています...'):
        try:
            import gen_animation
            st.success("更新完了！")
            st.rerun() 
        except Exception as e:
            st.error(f"実行エラー: {e}")

# --- メイン表示エリア：アニメーション ---
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
                    const alphaBase = Math.min(0.4, (frame - l.delay) / 320);
                    if (alphaBase > 0) {{
                        const n1 = data.nodes[l.source]; const n2 = data.nodes[l.target];
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
                    const alpha = Math.min(1.0, (frame - n.delay) / 120);
                    const x = mapX(n.x); const y = mapY(n.y);
                    const relFrame = (frame - n.delay) % RIPPLE_CYCLE;
                    const progress = relFrame / RIPPLE_CYCLE;
                    const rPx = (progress * (n.score * 4.5) / RANGE) * size;
                    
                    if (progress < 1.0) {{
                        ctx.beginPath();
                        ctx.arc(x, y, rPx, 0, Math.PI * 2);
                        ctx.strokeStyle = n.color;
                        ctx.lineWidth = 3.0; 
                        ctx.globalAlpha = 1.0 - progress;
                        ctx.stroke();
                        ctx.globalAlpha = 1.0;
                    }}

                    // --- 二重の白円グロウ効果 (透明度を下げて濃く修正) ---
                    // 外側の大きな円 (0.05 -> 0.10)
                    ctx.beginPath();
                    ctx.arc(x, y, (80/RANGE * size / 2), 0, Math.PI*2);
                    ctx.fillStyle = "rgba(255, 255, 255, " + (alpha * 0.1) + ")";
                    ctx.fill();
                    
                    // 内側の円 (0.15 -> 0.30)
                    ctx.beginPath();
                    ctx.arc(x, y, (40/RANGE * size / 2 * 0.7), 0, Math.PI*2);
                    ctx.fillStyle = "rgba(255, 255, 255, " + (alpha * 0.3) + ")";
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
else:
    st.info("👈 サイドバーから「アニメーションを生成」ボタンを押してください。")

# --- メイン表示エリア：静止画 (Zoom機能) ---
static_glow_path = "static_network_glow.png"
if os.path.exists(static_glow_path):
    st.subheader("静止画 (Motionless) - Zoomable")
    with open(static_glow_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode()
    
    html_static = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ margin: 0; overflow: hidden; background-color: #020617; display: flex; justify-content: center; align-items: center; height: 100vh; }}
        #container {{ width: 100%; height: 100%; max-width: 750px; aspect-ratio: 1 / 1; overflow: hidden; position: relative; }}
        img {{ transform-origin: 0 0; width: 100%; height: 100%; object-fit: contain; display: block; pointer-events: none; }}
    </style>
    </head>
    <body>
        <div id="container">
            <img id="zoom-img" src="data:image/png;base64,{img_data}" />
        </div>
        <script>
            const container = document.getElementById('container');
            const img = document.getElementById('zoom-img');
            let scale = 1, pointX = 0, pointY = 0;
            function update() {{ img.style.transform = `translate(${{pointX}}px, ${{pointY}}px) scale(${{scale}})`; }}
            container.addEventListener('wheel', (e) => {{
                if (e.ctrlKey) {{
                    e.preventDefault();
                    const rect = container.getBoundingClientRect();
                    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
                    const xs = (mx - pointX) / scale, ys = (my - pointY) / scale;
                    const factor = e.deltaY > 0 ? 0.9 : 1.1;
                    scale = Math.min(Math.max(1, scale * factor), 20);
                    pointX = mx - xs * scale; pointY = my - ys * scale;
                    if (scale === 1) {{ pointX = 0; pointY = 0; }}
                    update();
                }}
            }}, {{ passive: false }});
        </script>
    </body>
    </html>
    """
    components.html(html_static, height=750)

st.divider()
if os.path.exists("survey_data.csv"):
    st.subheader("📊 データフォーマット")
    st.dataframe(pd.read_csv("survey_data.csv"))
