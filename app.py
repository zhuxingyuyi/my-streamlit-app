import streamlit as st
import streamlit.components.v1 as components
import pd as pd
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

selected_colors = []
json_path = "animation_data.json"

if os.path.exists(json_path):
    with open(json_path, "r", encoding='utf-8') as f:
        tmp_data = json.load(f)
    
    # カテゴリー名でのフィルター機能
    if os.path.exists("survey_data.csv"):
        df_sample = pd.read_csv("survey_data.csv")
        if 'Q4_Switch' in df_sample.columns:
            categories = sorted(df_sample['Q4_Switch'].unique())
            label_to_color = {}
            # データから色とカテゴリーの紐付けを学習
            for node in tmp_data['nodes']:
                for cat in categories:
                    # gen_animation側のロジックと整合性をとるため、ノードの属性を確認
                    # ここでは簡易的に色を収集
                    label_to_color[cat] = node['color'] 
            
            st.sidebar.subheader("🎯 カテゴリー表示")
            selected_labels = st.sidebar.multiselect(
                "表示するカテゴリーを選択",
                options=list(label_to_color.keys()),
                default=[]
            )
            selected_colors = [label_to_color[lbl] for lbl in selected_labels]

st.sidebar.divider()

if st.sidebar.button("🎥 アニメーションを生成/更新"):
    with st.spinner('更新中...'):
        try:
            import gen_animation
            st.success("完了！")
            st.rerun() 
        except Exception as e:
            st.error(f"エラー: {e}")

# --- メイン表示エリア：アニメーション ---
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
        const DURATION_FRAMES = 8000; // 演出のため少し長めに設定
        const RIPPLE_CYCLE = 640; 
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
            frame = (timestamp - startTime) / 50;
            ctx.imageSmoothingEnabled = false; 

            // --- 演出：背景の星の瞬き ---
            // サイン波を使って、背景の明るさをゆっくり周期的に変化させる
            const twinkle = 0.85 + Math.sin(timestamp / 1000) * 0.15;
            ctx.globalAlpha = twinkle;
            
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
            ctx.globalAlpha = 1.0; // リセット

            // 線の描画
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
            
            // 点と波紋の描画
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

                    // 二重グロウ効果
                    ctx.beginPath();
                    ctx.arc(x, y, (80/RANGE * size / 2), 0, Math.PI*2);
                    ctx.fillStyle = "rgba(255, 255, 255, " + (alpha * 0.075) + ")";
                    ctx.fill();
                    ctx.beginPath();
                    ctx.arc(x, y, (40/RANGE * size / 2 * 0.7), 0, Math.PI*2);
                    ctx.fillStyle = "rgba(255, 255, 255, " + (alpha * 0.2) + ")";
                    ctx.fill();
                    
                    // 中心点（ここもわずかに瞬かせる）
                    const pulse = 0.8 + Math.sin((timestamp + n.delay*50) / 500) * 0.2;
                    ctx.beginPath();
                    ctx.arc(x, y, 3, 0, Math.PI*2); 
                    ctx.fillStyle = "rgba(255, 255, 255, " + (alpha * 0.9 * pulse) + ")";
                    ctx.fill();
                    
                    ctx.fillStyle = "rgba(255, 255, 255, " + (alpha * 0.7) + ")";
                    ctx.font = 'bold 9px sans-serif'; 
                    ctx.fillText(n.name, x + 8, y - 5);
                }}
            }});
            requestAnimationFrame(loop);
        }}
    </script>
    </body>
    </html>
    """
    components.html(html_code, height=750, scrolling=False)

# --- 静止画エリア (変更なし) ---
# ...（以下、前回のコードと同様に静止画部分を維持）
