import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import shutil

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
    with st.spinner('データを更新しています...'): # Much faster now
        try:
            import subprocess
            cmd = ["python", "gen_animation.py"]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                st.success("更新完了！")
            else:
                st.error(f"エラーが発生しました: {result.stderr}")
        except Exception as e:
            st.error(f"実行エラー: {e}")

# --- メイン表示エリア ---

# アニメーション表示
json_path = "animation_data.json"
bg_path = "universe_bg.png"

if os.path.exists(json_path):
    st.subheader("共鳴アニメーション (Real-time Render)")
    
    import json
    import base64
    import streamlit.components.v1 as components

    with open(json_path, "r", encoding='utf-8') as f:
        animation_data = json.load(f)
    
    bg_b64 = ""
    if os.path.exists(bg_path):
        with open(bg_path, "rb") as f:
            bg_b64 = base64.b64encode(f.read()).decode('utf-8')
            
    # Pass data to JS via template
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ margin: 0; background-color: #020617; overflow: hidden; width: 100vw; height: 100vh; display: flex; justify-content: center; align-items: center; }}
        canvas {{ 
            width: 100%; 
            height: 100%; 
            display: block;
        }}
    </style>
    </head>
    <body>
    <canvas id="canvas"></canvas>
    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        
        // Data from Python
        const data = {json.dumps(animation_data)};
        const bgData = "data:image/png;base64,{bg_b64}";
        
        // Config
        const LIMIT = 500; // -500 to 500
        const RANGE = 1000;
        const FPS = 20; // Original simulation FPS
        const DURATION_FRAMES = 4000; // 200s (Extended x2)
        const RIPPLE_CYCLE = 640; 
        
        let frame = 0;
        let startTime = null;
        let bgImage = new Image();
        
        bgImage.onload = () => {{
            requestAnimationFrame(loop);
        }};
        bgImage.src = bgData;
        
        let size = 1000;
        let offsetX = 0;
        let offsetY = 0;

        function resize() {{
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            
            // Calculate scale to fit simulation (RANGE=1000) into min dimension
            // BUT user wants "Animation Target Range" to cover screen?
            // If we just center, corners are empty.
            // PROPOSAL: Scale so RANGE fits the *smallest* dimension (contain) OR *largest* (cover)?
            // Usually "contain" ensures all nodes are visible. 
            // "Target Range" usually means the simulation coordinate system maps to the screen?
            // We will stick to "contain" logic for safety so nodes don't go offscreen, 
            // but the background will fill the screen.
            
            size = Math.min(canvas.width, canvas.height);
            offsetX = (canvas.width - size) / 2;
            offsetY = (canvas.height - size) / 2;
        }}
        window.addEventListener('resize', resize);
        resize();
        
        function mapX(x) {{
            return offsetX + ((x + LIMIT) / RANGE) * size;
        }}
        
        function mapY(y) {{
            // Invert Y
            return offsetY + size * (1 - (y + LIMIT) / RANGE);
        }}

        function loop(timestamp) {{
            if (!startTime) startTime = timestamp;
            const elapsed = timestamp - startTime;
            
            // Sync frame to elapsed time (50ms per frame)
            frame = Math.floor(elapsed / 50);
            
            // Draw Background (Cover Mode)
            const bgRatio = bgImage.width / bgImage.height;
            const canvasRatio = canvas.width / canvas.height;
            let dw, dh, dx, dy;
            
            if (canvasRatio > bgRatio) {{
                dw = canvas.width;
                dh = canvas.width / bgRatio;
                dx = 0;
                dy = (canvas.height - dh) / 2;
            }} else {{
                dh = canvas.height;
                dw = canvas.height * bgRatio;
                dx = (canvas.width - dw) / 2;
                dy = 0;
            }}
            ctx.drawImage(bgImage, dx, dy, dw, dh);
            
            // Helper to get alpha
            function getAlpha(delay) {{
                if (frame < delay) return 0;
                return Math.min(1.0, (frame - delay) / 120); 
            }}
            
            // Draw Lines
            data.lines.forEach(l => {{
                if (frame >= l.delay) {{
                    const alphaBase = Math.min(0.4, (frame - l.delay) / 320);
                    if (alphaBase > 0) {{
                        const n1 = data.nodes[l.source];
                        const n2 = data.nodes[l.target];
                        
                        ctx.beginPath();
                        ctx.moveTo(mapX(n1.x), mapY(n1.y));
                        ctx.lineTo(mapX(n2.x), mapY(n2.y));
                        ctx.strokeStyle = `rgba(255, 247, 214, ${{alphaBase}})`;
                        ctx.lineWidth = 1.0; 
                        ctx.stroke();
                    }}
                }}
            }});
            
            // Draw Nodes & Ripples
            data.nodes.forEach(n => {{
                if (frame >= n.delay) {{
                    const alpha = getAlpha(n.delay);
                    const x = mapX(n.x);
                    const y = mapY(n.y);
                    
                    // Ripple
                    const relFrame = (frame - n.delay) % RIPPLE_CYCLE;
                    const maxR = n.score * 4.5;
                    const progress = relFrame / RIPPLE_CYCLE;
                    const r = progress * maxR; 
                    // Map size: relative to the simulation scale 'size'
                    const rPx = (r / RANGE) * size;
                    
                    const rippleAlpha = Math.max(0, 1.0 * (1 - progress));
                    
                    if (rippleAlpha > 0) {{
                        ctx.beginPath();
                        ctx.arc(x, y, rPx, 0, Math.PI * 2);
                        ctx.strokeStyle = n.color;
                        ctx.lineWidth = 5.0 * (size / 1000); 
                        ctx.globalAlpha = rippleAlpha;
                        ctx.stroke();
                        ctx.globalAlpha = 1.0;
                    }}
                    
                    // Star Glow
                    ctx.beginPath();
                    ctx.arc(x, y, 80/RANGE * size / 2, 0, Math.PI*2); 
                    ctx.fillStyle = `rgba(255, 247, 214, ${{alpha * 0.075}})`;
                    ctx.fill();
                    
                    ctx.beginPath();
                    ctx.arc(x, y, 40/RANGE * size / 2 * 0.7, 0, Math.PI*2);
                    ctx.fillStyle = `rgba(255, 247, 214, ${{alpha * 0.2}})`;
                    ctx.fill();

                    // Star Core
                    ctx.beginPath();
                    ctx.arc(x, y, 3, 0, Math.PI*2); 
                    ctx.fillStyle = `rgba(255, 255, 255, ${{alpha * 0.9}})`;
                    ctx.fill();
                    
                    // Name
                    ctx.fillStyle = `rgba(255, 247, 214, ${{alpha * 0.8}})`;
                    ctx.font = 'bold 10px sans-serif';
                    ctx.fillText(n.name, x + 5, y - 5);
                }}
            }});
            
            if (frame < DURATION_FRAMES) {{
                requestAnimationFrame(loop);
            }}
        }}
        
        requestAnimationFrame(loop);
    </script>
    </body>
    </html>
    """
    
    components.html(html_code, height=750, scrolling=False)

else:
    st.info("👈 サイドバーから「アニメーションを生成」ボタンを押してください。")

# --- 静止画 (Glow Style) ---
static_glow_path = "static_network_glow.png"
if os.path.exists(static_glow_path):
    st.subheader("静止画 (Motionless) - Zoomable")
    
    import base64
    with open(static_glow_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode()
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ margin: 0; overflow: hidden; background-color: #020617; display: flex; justify-content: center; align-items: center; height: 100vh; }}
        #container {{
            width: 100%;
            height: 100%;
            max-width: 750px;
            aspect-ratio: 1 / 1;
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
        }}
        img {{
            transform-origin: 0 0;
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
            pointer-events: none;
        }}
    </style>
    </head>
    <body>
        <div id="container">
            <img id="zoom-img" src="data:image/png;base64,{img_data}" />
        </div>
        <script>
            const container = document.getElementById('container');
            const img = document.getElementById('zoom-img');
            
            let scale = 1;
            let pointX = 0;
            let pointY = 0;

            function updateTransform() {{
                img.style.transform = `translate(${{pointX}}px, ${{pointY}}px) scale(${{scale}})`;
            }}

            container.addEventListener('wheel', (e) => {{
                if (e.ctrlKey) {{
                    e.preventDefault();
                    
                    const rect = container.getBoundingClientRect();
                    const mx = e.clientX - rect.left;
                    const my = e.clientY - rect.top;
                    
                    const xs = (mx - pointX) / scale;
                    const ys = (my - pointY) / scale;
                    
                    const delta = -e.deltaY;
                    const factor = delta > 0 ? 1.1 : 0.9;
                    
                    let nextScale = scale * factor;
                    
                    if (nextScale < 1) nextScale = 1;
                    if (nextScale > 20) nextScale = 20;

                    pointX = mx - xs * nextScale;
                    pointY = my - ys * nextScale;
                    
                    if (nextScale === 1) {{
                        pointX = 0;
                        pointY = 0;
                    }}

                    scale = nextScale;
                    updateTransform();
                }}
            }}, {{ passive: false }});
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=750)

st.divider()

# --- データフォーマット案内 ---
st.subheader("📊 データフォーマット")
st.write("CSVファイルは以下の形式である必要があります。")

# Load current data to show as sample
if os.path.exists("survey_data.csv"):
    df = pd.read_csv("survey_data.csv")
    st.dataframe(df)
    
    # Download button for current CSV
    with open("survey_data.csv", "rb") as f:
        st.download_button(
            label="現在のCSVをダウンロード (サンプルとして利用可)",
            data=f,
            file_name="survey_data.csv",
            mime="text/csv"
        )
else:
    st.warning("データファイル (survey_data.csv) が見つかりません。")

st.markdown("""
### カラム説明
- **Name**: 表示される名前 (英数字推奨)
- **Q2**: 波紋の大きさ・勢い (数値 1-10推奨)
- **Q4_Switch**: 色を決定するスイッチ (安心, 挑戦, 確信, 充足, 静観)
- **Q5**: (内部計算用: リンクのつながりやすさ等)
- **Q6_Gift**: (予備)
""")
