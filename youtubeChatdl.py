# youtubeChatdl.py
import re
import json
import time
import sqlite3
import requests
from yt_dlp import YoutubeDL

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"


def fetch_html(url):
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.text


def extract_params(html):
    key_m = re.search(r'INNERTUBE_API_KEY["\']\s*:\s*"([^"]+)"', html)
    ver_m = re.search(r'INNERTUBE_CONTEXT_CLIENT_VERSION["\']\s*:\s*"([^"]+)"', html)
    yid_m = re.search(
        r'ytInitialData["\']?\s*[:=]\s*(\{.*?\})[;\n]', html, flags=re.DOTALL
    )

    api_key = key_m.group(1) if key_m else None
    version = ver_m.group(1) if ver_m else "2.20201021.03.00"
    yid = json.loads(yid_m.group(1)) if yid_m else None
    return api_key, version, yid


def find_continuation(ytInitialData):
    def walk(d):
        if isinstance(d, dict):
            if "continuation" in d:
                return d["continuation"]
            for v in d.values():
                res = walk(v)
                if res:
                    return res
        elif isinstance(d, list):
            for i in d:
                res = walk(i)
                if res:
                    return res
        return None

    return walk(ytInitialData)


def fetch_chat(api_key, version, continuation, retries=3):
    url = f"https://www.youtube.com/youtubei/v1/live_chat/get_live_chat_replay?key={api_key}"
    data = {
        "context": {"client": {"clientName": "WEB", "clientVersion": version}},
        "continuation": continuation,
    }
    headers = {"User-Agent": USER_AGENT, "Content-Type": "application/json"}
    for attempt in range(retries):
        try:
            r = requests.post(url, headers=headers, json=data, timeout=60)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ {type(e).__name__}: {e} — 重试 {attempt+1}/{retries}")
            time.sleep(3)
    raise RuntimeError("❌ 重试后仍无法获取。")


def ms_to_timestamp(ms):
    """将毫秒转换为 0:00 格式"""
    try:
        s = int(ms) // 1000
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
    except:
        return "0:00"


def init_database(db_path):
    """初始化SQLite数据库"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time_text TEXT,
            author TEXT,
            author_id TEXT,
            message TEXT,
            offset_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_offset ON chat_messages(offset_ms)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_author_id ON chat_messages(author_id)
    ''')
    conn.commit()
    return conn


def parse_messages(actions):
    """解析消息，不过滤负时间戳"""
    messages = []
    latest_offset = 0
    for a in actions or []:
        if "replayChatItemAction" in a:
            item = a["replayChatItemAction"].get("actions", [{}])[0]
            chat = item.get("addChatItemAction", {}).get("item", {})
            for t in ("liveChatTextMessageRenderer", "liveChatPaidMessageRenderer"):
                if t in chat:
                    r = chat[t]

                    author = r.get("authorName", {}).get("simpleText", "").strip()
                    if not author:
                        continue

                    # 获取作者频道ID
                    author_id = r.get("authorExternalChannelId", "")

                    msg_runs = r.get("message", {}).get("runs", [])
                    msg = "".join([x.get("text", "") for x in msg_runs]).strip()
                    if not msg:
                        continue

                    # 获取时间戳（不过滤负时间）
                    offset = 0
                    time_text = "0:00"
                    if "videoOffsetTimeMsec" in r:
                        try:
                            offset = int(float(r["videoOffsetTimeMsec"]))
                            time_text = ms_to_timestamp(offset)
                        except:
                            pass
                    elif "timestampText" in r:
                        time_text = r["timestampText"].get("simpleText", "0:00").strip()

                    # 删除非法字符
                    msg = re.sub(r"[\x00-\x1F\x7F]", "", msg)

                    messages.append((time_text, author, author_id, msg, offset))
                    if offset > latest_offset:
                        latest_offset = offset
    return messages, latest_offset


def extract_next_cont(json_data):
    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "continuation":
                    return v
                res = walk(v)
                if res:
                    return res
        elif isinstance(obj, list):
            for i in obj:
                res = walk(i)
                if res:
                    return res
        return None

    return walk(json_data)


def main(url):
    print(f"▶ Fetching: {url}")
    ydl_opts = {
        'cookiefile': 'www.youtube.com_cookies.txt'  # <-- 在这里设置 cookie 文件路径
    }
    # 🎬 获取视频信息（获取时长秒数）
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        duration = info.get("duration", 0)
        video_id = info.get("id", "unknown")
    print(f"📏 视频长度: {duration} 秒")

    html = fetch_html(url)
    api_key, version, yid = extract_params(html)
    if not yid:
        print("❌ 未找到 ytInitialData。可能需要 Cookie。")
        return

    continuation = find_continuation(yid)
    if not continuation:
        print("❌ 未找到 continuation。")
        return

    # 初始化数据库
    db_path = f"chatlog_{video_id}.db"
    conn = init_database(db_path)
    cursor = conn.cursor()
    
    total = 0
    max_seen_offset = 0
    seen_continuations = set()

    print("开始获取聊天消息...")

    start_time = time.time()
    for i in range(3000):
        if continuation in seen_continuations:
            print("🔁 由于重复相同的 continuation，已终止。")
            break
        seen_continuations.add(continuation)

        data = fetch_chat(api_key, version, continuation)
        actions = data.get("actions") or data.get("continuationContents", {}).get(
            "liveChatContinuation", {}
        ).get("actions")
        msgs, latest_offset = parse_messages(actions)

        if latest_offset > max_seen_offset:
            max_seen_offset = latest_offset

        if max_seen_offset / 1000 >= duration:
            print(f"🏁 已到达视频时间（{duration}s），已终止。")
            break

        # 批量插入数据库
        for time_text, author, author_id, msg, offset in msgs:
            cursor.execute('''
                INSERT INTO chat_messages (time_text, author, author_id, message, offset_ms)
                VALUES (?, ?, ?, ?, ?)
            ''', (time_text, author, author_id, msg, offset))
            total += 1
            print(f"{time_text} | {author} ({author_id}) | {msg}", flush=True)
        
        conn.commit()

        next_c = extract_next_cont(data)
        if not next_c:
            print("🟢 已无更多 continuation，已终止。")
            break
        continuation = next_c

        if i % 20 == 0:
            elapsed = int(time.time() - start_time)
            print(f"⏳ 已用时 {elapsed}s / 已获取 {total} 条 / 当前 {max_seen_offset//1000}s")

        time.sleep(0.08)

    print(f"✅ 完成：已将 {total} 条评论保存到 {db_path}。")

    # 显示统计信息
    cursor.execute('SELECT COUNT(*) FROM chat_messages')
    total_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT author_id) FROM chat_messages WHERE author_id != ""')
    unique_authors = cursor.fetchone()[0]
    
    cursor.execute('SELECT MIN(offset_ms), MAX(offset_ms) FROM chat_messages')
    min_offset, max_offset = cursor.fetchone()
    
    print(f"\n📊 统计信息:")
    print(f"   总消息数: {total_count}")
    print(f"   独特用户数: {unique_authors}")
    print(f"   时间范围: {ms_to_timestamp(min_offset if min_offset else 0)} - {ms_to_timestamp(max_offset if max_offset else 0)}")
    
    conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python youtubeChatdl.py <youtube_url>")
    else:
        main(sys.argv[1])
