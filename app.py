import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import json
import base64

# ページ設定
st.set_page_config(page_title="ファイブエムOS 可視化プロト", layout="wide")

# --- タイトルと説明 ---
st.title("ファイブエムOS 可視化プロト")
st.write("アンケート結果を『共鳴のエコー』として可視化します。")

# --- サイドバー：データ管理 ---
st.sidebar.header("データ管理")

uploaded_file = st.sidebar.file_uploader("新しいデータをアップロード (CSV)", type="csv")
if uploaded_file is not None:
    with open("survey_data.csv", "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success("データが保存されました！")

if st.sidebar.button("アニメーションを生成/更新"):
    with st.spinner('データを解析中...'):
        try:
            import gen_animation
            st.success("更新完了！")
            st.rerun() 
        except Exception as e:
            st.error(f"実行エラー: {e}")

# --- データの準備 ---
json_path = "animation_data.json"
bg_path = "universe_bg.png"
animation_data_json = "{}"
bg_b64 = ""

if os.path.exists(json_path):
    with open(json_path, "r", encoding='utf-8') as f:
        anim_data = json.load(f)
    
    if os.path.exists("survey_data.csv"):
        df_csv = pd.read_csv("survey_data.csv")
        gift_map = pd.Series(df_csv.Q6_Gift.values, index=df_csv.Name).to_dict()
        for node in anim_data['nodes']:
            node['gift'] = gift_map.get(node['name'], "メッセージはありません")
    
    animation_data_json = json.dumps(anim_data)

if os.path.exists(bg_path):
    with open(bg_path, "rb") as f:
        bg_b64 = base64.b64encode(f.read()).decode('utf-8')

# --- 1. スタンダード・アニメーション ---
if os.path.exists(json_path):
    st.subheader("スタンダード・アニメーション")
    html_standard = f"""
    <!DOCTYPE html><html><head><style>
        body {{ margin: 0; background-color: #020617; overflow: hidden; display: flex; justify-content: center; align-items: center; height: 600px; }}
        canvas {{ display: block; width: 800px; height: 600px; image-rendering: -webkit-optimize-contrast; }}
    </style></head><body>
    <canvas id="canvas_std"></canvas>
    <script>
        const canvas = document.getElementById('canvas_std');
        const ctx = canvas.getContext('2d');
        const data = {animation_data_json};
        const bgData = "data:image/png;base64,{bg_b64}";
        let startTime = Date.now();
        let bgImage = new Image();
        function resize() {{
            const dpr = window.devicePixelRatio || 1;
            canvas.width = 800 * dpr; canvas.height = 600 * dpr;
            ctx.scale(dpr, dpr);
        }}
        resize();
        bgImage.src = bgData;
        bgImage.onload = () => requestAnimationFrame(loop);

        function loop() {{
            const elapsed = (Date.now() - startTime) / 50;
            ctx.clearRect(0,0,800,600);
            ctx.drawImage(bgImage, 0, 0, 800, 600);
            data.lines.forEach(l => {{
                if (elapsed >= l.delay) {{
                    const n1 = data.nodes[l.source], n2 = data.nodes[l.target];
                    const a = Math.min(0.4, (elapsed - l.delay) / 320);
                    ctx.beginPath();
                    ctx.moveTo(100+((n1.x+500)/1000)*600, 600*(1-(n1.y+500)/1000));
                    ctx.lineTo(100+((n2.x+500)/1000)*600, 600*(1-(n2.y+500)/1000));
                    ctx.strokeStyle = "rgba(255, 255, 255, "+a+")"; ctx.lineWidth = 1; ctx.stroke();
                }}
            }});
            data.nodes.forEach(n => {{
                if (elapsed >= n.delay) {{
                    const a = Math.min(1.0, (elapsed - n.delay) / 120);
                    const x = 100+((n.x+500)/1000)*600, y = 600*(1-(n.y+500)/1000);
                    const p = ((elapsed - n.delay) % 640) / 640;
                    ctx.beginPath(); ctx.arc(x, y, (p*(n.score*4.5)/1000)*600, 0, Math.PI*2);
                    ctx.strokeStyle = n.color; ctx.lineWidth = 3; ctx.globalAlpha = Math.max(0, 1.2*(1-p)); ctx.stroke(); ctx.globalAlpha = 1;
                    ctx.beginPath(); ctx.arc(x, y, 24, 0, Math.PI*2); ctx.fillStyle = "rgba(255,255,255,"+(a*0.075)+")"; ctx.fill();
                    ctx.beginPath(); ctx.arc(x, y, 8, 0, Math.PI*2); ctx.fillStyle = "rgba(255,255,255,"+(a*0.2)+")"; ctx.fill();
                    ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI*2); ctx.fillStyle = "rgba(255,255,255,"+(a*0.9)+")"; ctx.fill();
                    ctx.fillStyle = "rgba(255,255,255,"+(a*0.7)+")"; ctx.font = 'bold 9px sans-serif'; ctx.fillText(n.name, x+8, y-5);
                }}
            }});
            requestAnimationFrame(loop);
        }}
    </script></body></html>
    """
    components.html(html_standard, height=620)

# --- 2. インタラクティブ・分析 ---
st.divider()
st.subheader("インタラクティブ・分析")

if os.path.exists(json_path):
    all_colors = sorted(list(set([n['color'] for n in anim_data['nodes']])))
    selected_colors = st.multiselect("表示する色のカテゴリーを選択", options=all_colors, default=[])

    html_interactive = f"""
    <!DOCTYPE html><html><head><style>
        body {{ margin: 0; background-color: #020617; overflow: hidden; display: flex; justify-content: center; align-items: center; height: 700px; }}
        #container {{ width: 800px; height: 600px; overflow: hidden; position: relative; cursor: crosshair; }}
        canvas {{ display: block; image-rendering: -webkit-optimize-contrast; }}
    </style></head><body>
    <div id="container"><canvas id="canvas_int"></canvas></div>
    <script>
        const container = document.getElementById('container');
        const canvas = document.getElementById('canvas_int');
        const ctx = canvas.getContext('2d');
        const data = {animation_data_json};
        const activeColors = {json.dumps(selected_colors)};
        const bgData = "data:image/png;base64,{bg_b64}";
        
        if (!window.sessionStorage.getItem('animStartTime')) window.sessionStorage.setItem('animStartTime', Date.now());
        const startTime = parseInt(window.sessionStorage.getItem('animStartTime'));

        let bgImage = new Image();
        let scale = 1, viewX = 0, viewY = 0, isDragging = false, lastX = 0, lastY = 0, selectedNode = null;

        function resize() {{
            const dpr = window.devicePixelRatio || 1;
            canvas.width = 800 * dpr; canvas.height = 600 * dpr;
            canvas.style.width = '800px'; canvas.style.height = '600px';
            ctx.scale(dpr, dpr);
        }}
        resize();
        bgImage.src = bgData;
        bgImage.onload = () => requestAnimationFrame(loop);

        container.addEventListener('mousedown', e => {{ isDragging = true; lastX = e.clientX; lastY = e.clientY; }});
        window.addEventListener('mouseup', () => isDragging = false);
        window.addEventListener('mousemove', e => {{
            if (isDragging) {{
                viewX += (e.clientX - lastX) / scale; viewY += (e.clientY - lastY) / scale;
                lastX = e.clientX; lastY = e.clientY;
            }}
        }});
        container.addEventListener('wheel', e => {{
            if (e.ctrlKey) {{ e.preventDefault(); const z = e.deltaY > 0 ? 0.9 : 1.1; scale = Math.min(Math.max(1, scale * z), 10); }}
        }}, {{ passive: false }});

        container.addEventListener('click', e => {{
            const rect = container.getBoundingClientRect();
            const mx = (e.clientX - rect.left) / scale - viewX;
            const my = (e.clientY - rect.top) / scale - viewY;
            let found = null;
            data.nodes.forEach(n => {{
                const nx = 100+((n.x+500)/1000)*600, ny = 600*(1-(n.y+500)/1000);
                if (Math.sqrt((mx-nx)**2 + (my-ny)**2) < 15/scale) found = n;
            }});
            selectedNode = (selectedNode === found) ? null : found;
        }});

        function loop() {{
            const elapsed = (Date.now() - startTime) / 50;
            ctx.clearRect(0,0,800,600);
            ctx.save();
            ctx.scale(scale, scale); ctx.translate(viewX, viewY);
            ctx.drawImage(bgImage, 0, 0, 800, 600);
            
            data.lines.forEach(l => {{
                if (elapsed >= l.delay) {{
                    const n1 = data.nodes[l.source], n2 = data.nodes[l.target];
                    if (activeColors.length === 0 || activeColors.includes(n1.color) || activeColors.includes(n2.color)) {{
                        const a = Math.min(0.4, (elapsed - l.delay) / 320);
                        ctx.beginPath(); ctx.moveTo(100+((n1.x+500)/1000)*600, 600*(1-(n1.y+500)/1000));
                        ctx.lineTo(100+((n2.x+500)/1000)*600, 600*(1-(n2.y+500)/1000));
                        ctx.strokeStyle = "rgba(255, 255, 255, "+a+")"; ctx.lineWidth = 1/scale; ctx.stroke();
                    }}
                }}
            }});
            data.nodes.forEach(n => {{
                if (elapsed >= n.delay) {{
                    const isSel = activeColors.length === 0 || activeColors.includes(n.color);
                    const a = (isSel ? 1 : 0.1) * Math.min(1, (elapsed - n.delay)/120);
                    const x = 100+((n.x+500)/1000)*600, y = 600*(1-(n.y+500)/1000);
                    if (isSel) {{
                        const p = ((elapsed - n.delay) % 640) / 640;
                        ctx.beginPath(); ctx.arc(x, y, (p*(n.score*4.5)/1000)*600, 0, Math.PI*2);
                        ctx.strokeStyle = n.color; ctx.lineWidth = 3/scale; ctx.globalAlpha = Math.max(0, 1.2*(1-p)); ctx.stroke(); ctx.globalAlpha = 1;
                    }}
                    ctx.beginPath(); ctx.arc(x, y, 24, 0, Math.PI*2); ctx.fillStyle = "rgba(255,255,255,"+(a*0.075)+")"; ctx.fill();
                    ctx.beginPath(); ctx.arc(x, y, 8, 0, Math.PI*2); ctx.fillStyle = "rgba(255,255,255,"+(a*0.2)+")"; ctx.fill();
                    ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI*2); ctx.fillStyle = "rgba(255,255,255,"+(a*0.9)+")"; ctx.fill();
                    ctx.fillStyle = "rgba(255,255,255,"+(a*0.7)+")"; ctx.font = `bold ${{9/scale}}px sans-serif`; ctx.fillText(n.name, x+8/scale, y-5/scale);

                    if (selectedNode === n) {{
                        const txt = n.gift; 
                        ctx.font = `bold ${{10/scale}}px sans-serif`;
                        const tw = ctx.measureText(txt).width;
                        const bx = x - tw - 15/scale, by = y - 15/scale;
                        
                        // 1. 引き出し線（点からアンダーラインの右端へ）
                        ctx.beginPath(); 
                        ctx.moveTo(x - 4/scale, y - 4/scale); 
                        ctx.lineTo(bx + tw, by + 2/scale);
                        ctx.strokeStyle = "rgba(255, 255, 255, 0.7)"; 
                        ctx.lineWidth = 1/scale; 
                        ctx.stroke();
                        
                        // 2. テキスト表示（左上配置）
                        ctx.fillStyle = "white";
                        ctx.textAlign = "right"; 
                        ctx.fillText(txt, bx + tw, by);
                        
                        // 3. アンダーライン（下辺のみ）
                        ctx.beginPath();
                        ctx.moveTo(bx, by + 2/scale);
                        ctx.lineTo(bx + tw, by + 2/scale);
                        ctx.strokeStyle = "rgba(255, 255, 255, 0.9)";
                        ctx.lineWidth = 1/scale;
                        ctx.stroke();
                        
                        ctx.textAlign = "left"; // リセット
                    }}
                }}
            }});
            ctx.restore(); requestAnimationFrame(loop);
        }}
    </script></body></html>
    """
    components.html(html_interactive, height=720)

# --- 3. データテーブル ---
st.divider()
st.subheader("アンケート元データ")
if os.path.exists("survey_data.csv"):
    df = pd.read_csv("survey_data.csv")
    st.dataframe(df, use_container_width=True)

