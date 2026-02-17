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
    st.sidebar.success("データが保存されました！")

if st.sidebar.button("🎥 アニメーションを生成/更新"):
    with st.spinner('データを解析中...'):
        try:
            import gen_animation
            st.success("更新完了！")
            st.rerun() 
        except Exception as e:
            st.error(f"実行エラー: {e}")

# --- 共通変数の準備 ---
json_path = "animation_data.json"
bg_path = "universe_bg.png"
animation_data_json = "{}"
bg_b64 = ""

# CSVからQ6_Giftを取得してノードデータに紐付ける処理
if os.path.exists(json_path):
    with open(json_path, "r", encoding='utf-8') as f:
        anim_data = json.load(f)
    
    if os.path.exists("survey_data.csv"):
        df_csv = pd.read_csv("survey_data.csv")
        # 名前をキーにしてQ6_Giftを辞書化
        gift_map = pd.Series(df_csv.Q6_Gift.values, index=df_csv.Name).to_dict()
        # 各ノードにGift情報を追加
        for node in anim_data['nodes']:
            node['gift'] = gift_map.get(node['name'], "メッセージはありません")
            
    animation_data_json = json.dumps(anim_data)

if os.path.exists(bg_path):
    with open(bg_path, "rb") as f:
        bg_b64 = base64.b64encode(f.read()).decode('utf-8')

# --- 1. スタンダード・アニメーション ---
# （以前のコードと同様のため中略・必要であれば残してください）

# --- 2. カテゴリーフィルター付・アニメーション (ズーム＆クリック対応) ---
st.divider()
st.subheader("🔍 インタラクティブ・分析 (点を選択してメッセージを表示)")

if os.path.exists(json_path):
    all_colors = sorted(list(set([n['color'] for n in anim_data['nodes']])))
    selected_colors = st.multiselect("表示する色のカテゴリーを選択", options=all_colors, default=[])

    html_interactive = f"""
    <!DOCTYPE html><html><head><style>
        body {{ margin: 0; background-color: #020617; overflow: hidden; display: flex; justify-content: center; align-items: center; height: 700px; }}
        #container {{ width: 800px; height: 600px; overflow: hidden; position: relative; cursor: crosshair; }}
        canvas {{ display: block; }}
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
        const LIMIT = 500, RANGE = 1000, RIPPLE_CYCLE = 640;
        
        let scale = 1, viewX = 0, viewY = 0;
        let isDragging = false, lastMouseX = 0, lastMouseY = 0;
        let selectedNode = null; // クリックされたノード保持

        function resize() {{
            const dpr = window.devicePixelRatio || 1;
            canvas.width = 800 * dpr; canvas.height = 600 * dpr;
            canvas.style.width = '800px'; canvas.style.height = '600px';
            ctx.scale(dpr, dpr);
        }}
        resize();
        bgImage.src = bgData;
        bgImage.onload = () => requestAnimationFrame(loop);

        // クリックイベント（判定）
        container.addEventListener('click', (e) => {{
            if (isDragging && Math.abs(e.clientX - lastMouseX) > 5) return; // ドラッグ中は無視
            
            const rect = container.getBoundingClientRect();
            const mouseX = (e.clientX - rect.left);
            const mouseY = (e.clientY - rect.top);

            // 逆計算してシミュレーション座標上のマウス位置を特定
            const worldX = (mouseX / scale) - viewX;
            const worldY = (mouseY / scale) - viewY;

            let found = null;
            data.nodes.forEach(n => {{
                const nx = 100 + ((n.x + 500) / 1000) * 600;
                const ny = 600 * (1 - (n.y + 500) / 1000);
                const dist = Math.sqrt((worldX - nx)**2 + (worldY - ny)**2);
                if (dist < 15 / scale) found = n; // 判定距離
            }});
            selectedNode = found;
        }});

        container.addEventListener('mousedown', (e) => {{ isDragging = true; lastMouseX = e.clientX; lastMouseY = e.clientY; }});
        window.addEventListener('mouseup', () => {{ setTimeout(() => isDragging = false, 50); }});
        window.addEventListener('mousemove', (e) => {{
            if (isDragging) {{
                viewX += (e.clientX - lastMouseX) / scale;
                viewY += (e.clientY - lastMouseY) / scale;
                lastMouseX = e.clientX; lastMouseY = e.clientY;
            }}
        }});
        
        container.addEventListener('wheel', (e) => {{
            if (e.ctrlKey) {{
                e.preventDefault();
                const rect = container.getBoundingClientRect();
                const mouseX = (e.clientX - rect.left);
                const mouseY = (e.clientY - rect.top);
                const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
                const newScale = Math.min(Math.max(1, scale * zoomFactor), 10);
                viewX -= (mouseX / scale - mouseX / newScale);
                viewY -= (mouseY / scale - mouseY / newScale);
                scale = newScale;
                update();
            }}
        }}, {{ passive: false }});

        function loop() {{
            const elapsed = (Date.now() - startTime) / 50;
            ctx.clearRect(0,0,800,600);
            ctx.save();
            ctx.scale(scale, scale);
            ctx.translate(viewX, viewY);
            ctx.drawImage(bgImage, 0, 0, 800, 600);
            
            // 線描画
            data.lines.forEach(l => {{
                if (elapsed >= l.delay) {{
                    const n1 = data.nodes[l.source], n2 = data.nodes[l.target];
                    const isVis = activeColors.length === 0 || activeColors.includes(n1.color) || activeColors.includes(n2.color);
                    if (isVis) {{
                        const alpha = Math.min(0.4, (elapsed - l.delay) / 320);
                        ctx.beginPath(); 
                        ctx.moveTo(100+((n1.x+500)/1000)*600, 600*(1-(n1.y+500)/1000));
                        ctx.lineTo(100+((n2.x+500)/1000)*600, 600*(1-(n2.y+500)/1000));
                        ctx.strokeStyle = "rgba(255, 255, 255, " + alpha + ")"; ctx.lineWidth = 1/scale; ctx.stroke();
                    }}
                }}
            }});

            // ノード描画
            data.nodes.forEach(n => {{
                if (elapsed >= n.delay) {{
                    const isSel = activeColors.length === 0 || activeColors.includes(n.color);
                    const baseAlpha = Math.min(1.0, (elapsed - n.delay) / 120);
                    const alpha = isSel ? baseAlpha : baseAlpha * 0.1;
                    const x = 100+((n.x+500)/1000)*600, y = 600*(1-(n.y+500)/1000);
                    
                    if (isSel) {{
                        const relFrame = (elapsed - n.delay) % RIPPLE_CYCLE;
                        const progress = relFrame / RIPPLE_CYCLE;
                        ctx.beginPath(); ctx.arc(x, y, (progress * (n.score * 4.5) / 1000) * 600, 0, Math.PI*2);
                        ctx.strokeStyle = n.color; ctx.lineWidth = 3/scale; ctx.globalAlpha = Math.max(0, 1.2 * (1 - progress)); ctx.stroke(); ctx.globalAlpha = 1;
                    }}

                    // グロウ効果
                    ctx.beginPath(); ctx.arc(x, y, 24, 0, Math.PI*2); ctx.fillStyle = "rgba(255,255,255,"+(alpha*0.075)+")"; ctx.fill();
                    ctx.beginPath(); ctx.arc(x, y, 8, 0, Math.PI*2); ctx.fillStyle = "rgba(255,255,255,"+(alpha*0.2)+")"; ctx.fill();
                    ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI*2); ctx.fillStyle = "rgba(255,255,255,"+(alpha*0.9)+")"; ctx.fill();
                    
                    // 名前
                    ctx.fillStyle = "rgba(255,255,255,"+(alpha*0.7)+")"; 
                    ctx.font = `bold ${{9/scale}}px sans-serif`; 
                    ctx.fillText(n.name, x + 8/scale, y - 5/scale);

                    // ポップアップ表示（選択されたノードのみ）
                    if (selectedNode === n) {{
                        ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
                        ctx.font = `bold ${{10/scale}}px sans-serif`;
                        // 吹き出し背景
                        const txt = n.gift;
                        const tw = ctx.measureText(txt).width;
                        ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
                        ctx.fillRect(x - tw/2 - 5/scale, y - 25/scale, tw + 10/scale, 15/scale);
                        ctx.strokeStyle = "rgba(255, 255, 255, 0.5)";
                        ctx.lineWidth = 1/scale;
                        ctx.strokeRect(x - tw/2 - 5/scale, y - 25/scale, tw + 10/scale, 15/scale);
                        // テキスト
                        ctx.fillStyle = "white";
                        ctx.textAlign = "center";
                        ctx.fillText(txt, x, y - 14/scale);
                        ctx.textAlign = "left"; // リセット
                    }}
                }}
            }});
            ctx.restore();
            requestAnimationFrame(loop);
        }}
    </script></body></html>
    """
    components.html(html_interactive, height=650)
