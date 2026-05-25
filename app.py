import streamlit as st
import streamlit.components.v1 as components

# Cấu hình giao diện Streamlit
st.set_page_config(page_title="Tank Fight", layout="centered")

st.title("🪖 Tank Fight")
st.markdown("🧱 *BẢN CẬP NHẬT:* Đã thêm các khối chướng ngại vật ở giữa bản đồ! Hãy tận dụng để ẩn nấp né đạn.")

# Khởi tạo điểm số
if "score_p1" not in st.session_state:
    st.session_state.score_p1 = 0
if "score_p2" not in st.session_state:
    st.session_state.score_p2 = 0

# Thanh bên
st.sidebar.header("Cài Đặt")
mode = st.sidebar.radio("Chế độ chơi:", ("Đấu với Máy (PvE)", "Hai người chơi (PvP)"))

st.sidebar.markdown(f"""
### 🏆 ĐIỂM SỐ TÍCH LŨY:
* *P1:* {st.session_state.score_p1} | *P2/Máy:* {st.session_state.score_p2}
""")

# Ép trình duyệt tải lại toàn bộ trang từ đầu để xóa đơ khi bấm Reset
if st.sidebar.button("🔄 Reset Trận Đấu"):
    st.markdown('<meta http-equiv="refresh" content="0">', unsafe_allow_html=True)

if st.sidebar.button("❌ Xóa Điểm Số"):
    st.session_state.score_p1 = 0
    st.session_state.score_p2 = 0
    st.markdown('<meta http-equiv="refresh" content="0">', unsafe_allow_html=True)

is_pvp_flag = "true" if mode == "Hai người chơi (PvP)" else "false"

# Mã HTML + JS có chứa chướng ngại vật và logic va chạm nâng cao
game_html = f"""
<style>
    .game-container {{
        width: 100%;
        max-width: 600px;
        margin: 0 auto;
        text-align: center;
        font-family: sans-serif;
        touch-action: manipulation;
    }}
    canvas {{
        width: 100%;
        height: auto;
        background: #2c3e50;
        border: 4px solid #34495e;
        border-radius: 8px;
        cursor: pointer;
    }}
    .status-text {{ color: white; margin: 8px 0; }}
    
    .controls-wrapper {{
        display: flex;
        justify-content: space-around;
        margin-top: 15px;
        flex-wrap: wrap;
    }}
    .dpad {{
        display: grid;
        grid-template-columns: 52px 52px 52px;
        grid-template-rows: 52px 52px 52px;
        grid-gap: 6px;
    }}
    .btn-game {{
        background: #7f8c8d;
        color: white;
        border: none;
        border-radius: 10px;
        font-size: 20px;
        font-weight: bold;
        user-select: none;
        -webkit-user-select: none;
    }}
    .btn-game:active {{ background: #34495e; }}
    .btn-fire {{ grid-column: 2; grid-row: 2; background: #e67e22; }}
    .btn-fire:active {{ background: #d35400; }}
    .player-label {{ color: white; font-size: 14px; margin-bottom: 5px; }}
</style>

<div class="game-container" id="focusArea">
    <canvas id="gameCanvas" width="600" height="400" tabindex="1"></canvas>
    <h3 class="status-text" id="scoreboard">HP P1: 100 | HP P2/AI: 100</h3>
    <h4 style="color: #f1c40f; margin: 5px 0;" id="live-score">Điểm ván này - P1: 0 | P2: 0</h4>
    <h2 style="color: #2ecc71; font-weight: bold;" id="winner"></h2>

    <div class="controls-wrapper">
        <div>
            <div class="player-label" style="color: #3498db;">Điều khiển P1</div>
            <div class="dpad">
                <td></td> <button class="btn-game" id="btn-p1-up">↑</button> <td></td>
                <button class="btn-game" id="btn-p1-left">←</button>
                <button class="btn-game btn-fire" id="btn-p1-fire">🔥</button>
                <button class="btn-game" id="btn-p1-right">→</button>
                <td></td> <button class="btn-game" id="btn-p1-down">↓</button> <td></td>
            </div>
        </div>

        <div id="p2-ui-panel">
            <div class="player-label" id="p2-label-text" style="color: #e74c3c;">Điều khiển P2</div>
            <div class="dpad">
                <td></td> <button class="btn-game" id="btn-p2-up">↑</button> <td></td>
                <button class="btn-game" id="btn-p2-left">←</button>
                <button class="btn-game btn-fire" id="btn-p2-fire">🔥</button>
                <button class="btn-game" id="btn-p2-right">→</button>
                <td></td> <button class="btn-game" id="btn-p2-down">↓</button> <td></td>
            </div>
        </div>
    </div>
</div>

<script>
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");
const scoreText = document.getElementById("scoreboard");
const liveScoreText = document.getElementById("live-score");
const winnerText = document.getElementById("winner");
const p2Panel = document.getElementById("p2-ui-panel");
const p2LabelText = document.getElementById("p2-label-text");

window.focus();
canvas.focus();
document.addEventListener("click", () => {{ canvas.focus(); }});

const isPvP = {is_pvp_flag};
if (!isPvP) {{
    p2Panel.style.opacity = "0.2";
    p2LabelText.innerText = "Máy tự động";
}}

const tankSize = 32;
const bulletSpeed = 6;
const tankSpeed = 3;

let scoreP1 = 0;
let scoreP2 = 0;

// DANH SÁCH CHƯỚNG NGẠI VẬT (Mỗi khối gồm x, y, width, height)
const obstacles = [
    {{ x: 280, y: 40, w: 40, h: 100 }},  // Tường dọc phía trên
    {{ x: 280, y: 260, w: 40, h: 100 }}, // Tường dọc phía dưới
    {{ x: 120, y: 180, w: 60, h: 40 }},  // Tường ngang chắn góc trái
    {{ x: 420, y: 180, w: 60, h: 40 }}   // Tường ngang chắn góc phải
];

let p1 = {{ x: 40, y: 50, angle: 0, color: "#3498db", hp: 100, maxHp: 100, lastShot: 0, dx: 0, dy: 0, dirX: 1, dirY: 0 }};
let p2 = {{ x: 520, y: 310, angle: Math.PI, color: "#e74c3c", hp: 100, maxHp: 100, lastShot: 0, dx: 0, dy: 0, dirX: -1, dirY: 0, aiTimer: 0 }};

let bullets = [];
let keys = {{}};
let gameOver = false;

let touchControls = {{
    p1Up: false, p1Down: false, p1Left: false, p1Right: false,
    p2Up: false, p2Down: false, p2Left: false, p2Right: false
}};

// Bàn phím PC
canvas.addEventListener("keydown", (e) => {{
    keys[e.code] = true;
    if(["Space", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.code)) e.preventDefault();
}});
canvas.addEventListener("keyup", (e) => {{ keys[e.code] = false; }});

// Cảm ứng điện thoại
function setupTouchBtn(btnId, actionKey) {{
    const btn = document.getElementById(btnId);
    if(!btn) return;
    btn.addEventListener("touchstart", (e) => {{ e.preventDefault(); touchControls[actionKey] = true; }}, {{ passive: false }});
    btn.addEventListener("mousedown", (e) => {{ touchControls[actionKey] = true; }});
    btn.addEventListener("touchend", (e) => {{ e.preventDefault(); touchControls[actionKey] = false; }}, {{ passive: false }});
    btn.addEventListener("mouseup", (e) => {{ touchControls[actionKey] = false; }});
    btn.addEventListener("mouseleave", (e) => {{ touchControls[actionKey] = false; }});
}}
setupTouchBtn("btn-p1-up", "p1Up"); setupTouchBtn("btn-p1-down", "p1Down");
setupTouchBtn("btn-p1-left", "p1Left"); setupTouchBtn("btn-p1-right", "p1Right");

if (isPvP) {{
    setupTouchBtn("btn-p2-up", "p2Up"); setupTouchBtn("btn-p2-down", "p2Down");
    setupTouchBtn("btn-p2-left", "p2Left"); setupTouchBtn("btn-p2-right", "p2Right");
}}

document.getElementById("btn-p1-fire").addEventListener("touchstart", (e) => {{ e.preventDefault(); shoot(p1); }}, {{ passive: false }});
document.getElementById("btn-p1-fire").addEventListener("click", () => {{ shoot(p1); }});

if (isPvP) {{
    document.getElementById("btn-p2-fire").addEventListener("touchstart", (e) => {{ e.preventDefault(); shoot(p2); }}, {{ passive: false }});
    document.getElementById("btn-p2-fire").addEventListener("click", () => {{ shoot(p2); }});
}}

// Hàm kiểm tra va chạm hình chữ nhật (AABB Collision)
function checkRectCollision(rect1, rect2) {{
    return rect1.x < rect2.x + rect2.w &&
           rect1.x + rect1.w > rect2.x &&
           rect1.y < rect2.y + rect2.h &&
           rect1.y + rect1.h > rect2.y;
}}

function shoot(tank) {{
    if (gameOver) return;
    let now = Date.now();
    if (now - tank.lastShot > 350) {{
        bullets.push({{
            x: tank.x + tankSize/2 + tank.dirX * (tankSize/2 + 4),
            y: tank.y + tankSize/2 + tank.dirY * (tankSize/2 + 4),
            vx: tank.dirX * bulletSpeed,
            vy: tank.dirY * bulletSpeed,
            owner: tank
        }});
        tank.lastShot = now;
    }}
}}

function updateInput() {{
    if (gameOver) return;

    p1.dx = 0; p1.dy = 0;
    if (keys["KeyW"] || touchControls.p1Up) {{ p1.dy = -tankSpeed; p1.dirX = 0; p1.dirY = -1; p1.angle = -Math.PI/2; }}
    else if (keys["KeyS"] || touchControls.p1Down) {{ p1.dy = tankSpeed; p1.dirX = 0; p1.dirY = 1; p1.angle = Math.PI/2; }}
    else if (keys["KeyA"] || touchControls.p1Left) {{ p1.dx = -tankSpeed; p1.dirX = -1; p1.dirY = 0; p1.angle = Math.PI; }}
    else if (keys["KeyD"] || touchControls.p1Right) {{ p1.dx = tankSpeed; p1.dirX = 1; p1.dirY = 0; p1.angle = 0; }}

    if (keys["Space"]) {{ shoot(p1); }}

    if (isPvP) {{
        p2.dx = 0; p2.dy = 0;
        if (keys["ArrowUp"] || touchControls.p2Up) {{ p2.dy = -tankSpeed; p2.dirX = 0; p2.dirY = -1; p2.angle = -Math.PI/2; }}
        else if (keys["ArrowDown"] || touchControls.p2Down) {{ p2.dy = tankSpeed; p2.dirX = 0; p2.dirY = 1; p2.angle = Math.PI/2; }}
        else if (keys["ArrowLeft"] || touchControls.p2Left) {{ p2.dx = -tankSpeed; p2.dirX = -1; p2.dirY = 0; p2.angle = Math.PI; }}
        else if (keys["ArrowRight"] || touchControls.p2Right) {{ p2.dx = tankSpeed; p2.dirX = 1; p2.dirY = 0; p2.angle = 0; }}
        if (keys["Enter"]) {{ shoot(p2); }}
    }} else {{
        p2.aiTimer++;
        if (p2.aiTimer > 18) {{
            p2.aiTimer = 0;
            let diffX = p1.x - p2.x; let diffY = p1.y - p2.y;
            
            // AI di chuyển có tính toán sơ bộ để không đâm đầu liên tục vào chướng ngại vật
            if (Math.abs(diffX) > Math.abs(diffY)) {{
                p2.dx = diffX > 0 ? tankSpeed : -tankSpeed; p2.dy = 0;
                p2.dirX = diffX > 0 ? 1 : -1; p2.dirY = 0; p2.angle = diffX > 0 ? 0 : Math.PI;
            }} else {{
                p2.dy = diffY > 0 ? tankSpeed : -tankSpeed; p2.dx = 0;
                p2.dirX = 0; p2.dirY = diffY > 0 ? 1 : -1; p2.angle = diffY > 0 ? Math.PI/2 : -Math.PI/2;
            }}
            if (Math.random() < 0.4) {{ shoot(p2); }}
        }}
    }}
}}

function updatePhysics() {{
    if (gameOver) return;

    // --- DI CHUYỂN VÀ XỬ LÝ VA CHẠM TƯỜNG CỦA P1 ---
    let nextP1X = Math.max(0, Math.min(canvas.width - tankSize, p1.x + p1.dx));
    let nextP1Y = Math.max(0, Math.min(canvas.height - tankSize, p1.y + p1.dy));
    let p1Box = {{ x: nextP1X, y: nextP1Y, w: tankSize, h: tankSize }};
    let p1Collided = false;
    
    for (let obs of obstacles) {{
        if (checkRectCollision(p1Box, obs)) {{ p1Collided = true; break; }}
    }}
    if (!p1Collided) {{ p1.x = nextP1X; p1.y = nextP1Y; }}

    // --- DI CHUYỂN VÀ XỬ LÝ VA CHẠM TƯỜNG CỦA P2 ---
    let nextP2X = Math.max(0, Math.min(canvas.width - tankSize, p2.x + p2.dx));
    let nextP2Y = Math.max(0, Math.min(canvas.height - tankSize, p2.y + p2.dy));
    let p2Box = {{ x: nextP2X, y: nextP2Y, w: tankSize, h: tankSize }};
    let p2Collided = false;
    
    for (let obs of obstacles) {{
        if (checkRectCollision(p2Box, obs)) {{ p2Collided = true; break; }}
    }}
    if (!p2Collided) {{ p2.x = nextP2X; p2.y = nextP2Y; }}

    // --- XỬ LÝ ĐẠN BAY VÀ VA CHẠM TƯỜNG ---
    for (let i = bullets.length - 1; i >= 0; i--) {{
        let b = bullets[i];
        b.x += b.vx; b.y += b.vy;

        // Đạn ra rìa bản đồ
        if (b.x < 0 || b.x > canvas.width || b.y < 0 || b.y > canvas.height) {{
            bullets.splice(i, 1); continue;
        }}

        // Đạn bắn trúng chướng ngại vật (Tường nuốt đạn)
        let bulletBox = {{ x: b.x - 2, y: b.y - 2, w: 4, h: 4 }};
        let hitWall = false;
        for (let obs of obstacles) {{
            if (checkRectCollision(bulletBox, obs)) {{ hitWall = true; break; }}
        }}
        if (hitWall) {{
            bullets.splice(i, 1); continue;
        }}

        // Đạn trúng P1
        if (b.owner !== p1 && b.x > p1.x && b.x < p1.x + tankSize && b.y > p1.y && b.y < p1.y + tankSize) {{
            p1.hp = Math.max(0, p1.hp - 10); scoreP2 += 10;
            bullets.splice(i, 1); checkGameOver(); continue;
        }}

        // Đạn trúng P2
        if (b.owner !== p2 && b.x > p2.x && b.x < p2.x + tankSize && b.y > p2.y && b.y < p2.y + tankSize) {{
            p2.hp = Math.max(0, p2.hp - 10); scoreP1 += 10;
            bullets.splice(i, 1); checkGameOver(); continue;
        }}
    }}

    scoreText.innerText = "HP P1: " + p1.hp + " | HP " + (isPvP ? "P2" : "MÁY") + ": " + p2.hp;
    liveScoreText.innerText = "Điểm ván này - P1: " + scoreP1 + " | " + (isPvP ? "P2" : "MÁY") + ": " + scoreP2;
}}

function checkGameOver() {{
    if (p1.hp <= 0) {{
        gameOver = true;
        winnerText.innerText = isPvP ? "🎉 NGƯỜI CHƠI 2 THẮNG!" : "🤖 MÁY ĐÃ THẮNG!";
    }} else if (p2.hp <= 0) {{
        gameOver = true;
        winnerText.innerText = "🎉 NGƯỜI CHƠI 1 THẮNG!";
    }}
}}

// Hàm vẽ chướng ngại vật gạch cổ điển
function drawObstacles() {{
    ctx.fillStyle = "#e67e22"; // Màu cam gạch nung
    ctx.strokeStyle = "#d35400"; // Viền gạch sẫm
    ctx.lineWidth = 2;

    obstacles.forEach(obs => {{
        ctx.fillRect(obs.x, obs.y, obs.w, obs.h);
        ctx.strokeRect(obs.x, obs.y, obs.w, obs.h);

        // Vẽ thêm một vài đường vân gạch giả lập cho đẹp mắt
        ctx.strokeStyle = "rgba(255,255,255,0.2)";
        ctx.lineWidth = 1;
        for (let i = obs.y + 10; i < obs.y + obs.h; i += 15) {{
            ctx.beginPath(); ctx.moveTo(obs.x, i); ctx.lineTo(obs.x + obs.w, i); ctx.stroke();
        }}
    }});
}}

function drawHealthBar(tank) {{
    const barWidth = tankSize + 8; const barHeight = 5;
    const barX = tank.x - 4; const barY = tank.y - 12;
    ctx.fillStyle = "#c0392b"; ctx.fillRect(barX, barY, barWidth, barHeight);
    const currentHealthWidth = (tank.hp / tank.maxHp) * barWidth;
    ctx.fillStyle = "#2ecc71"; ctx.fillRect(barX, barY, currentHealthWidth, barHeight);
    ctx.strokeStyle = "#000"; ctx.strokeRect(barX, barY, barWidth, barHeight);
}}

function drawTank(tank) {{
    drawHealthBar(tank);
    ctx.save();
    ctx.translate(tank.x + tankSize/2, tank.y + tankSize/2);
    ctx.rotate(tank.angle);
    ctx.fillStyle = tank.color;
    ctx.fillRect(-tankSize/2, -tankSize/2, tankSize, tankSize);
    ctx.fillStyle = "#111";
    ctx.fillRect(-tankSize/2, -tankSize/2 - 2, tankSize, 4);
    ctx.fillRect(-tankSize/2, tankSize/2 - 2, tankSize, 4);
    ctx.beginPath(); ctx.arc(0, 0, tankSize/4, 0, Math.PI * 2); ctx.fillStyle = "#fff"; ctx.fill();
    ctx.fillStyle = "#ecf0f1"; ctx.fillRect(0, -3, tankSize/2 + 6, 6);
    ctx.restore();
}}

function gameLoop() {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Vẽ chướng ngại vật trước để xe tăng đè lên trên thanh máu nếu chạm sát
    drawObstacles();

    updateInput();
    updatePhysics();

    drawTank(p1); drawTank(p2);

    ctx.fillStyle = "#f1c40f";
    bullets.forEach(b => {{
        ctx.beginPath(); ctx.arc(b.x, b.y, 4, 0, Math.PI*2); ctx.fill();
    }});

    requestAnimationFrame(gameLoop);
}}

gameLoop();
</script>
"""

components.html(game_html, height=760)
