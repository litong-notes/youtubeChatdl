# youtubeChatdl.py
import re
import json
import time
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


def parse_messages(actions):
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

                    msg_runs = r.get("message", {}).get("runs", [])
                    msg = "".join([x.get("text", "") for x in msg_runs]).strip()
                    if not msg:
                        continue

                    # 获取时间戳（完全跳过负时间）
                    offset = 0
                    time_text = "0:00"
                    if "videoOffsetTimeMsec" in r:
                        try:
                            offset = int(float(r["videoOffsetTimeMsec"]))
                            if offset < 0:
                                continue  # 🧹 排除负时间评论
                            time_text = ms_to_timestamp(offset)
                        except:
                            pass
                    elif "timestampText" in r:
                        time_text = r["timestampText"].get("simpleText", "0:00").strip()
                        if time_text.startswith(
                            "-"
                        ):  # ✅ 检测负号标记并跳过
                            continue

                    # 删除非法字符
                    msg = re.sub(r"[\x00-\x1F\x7F]", "", msg)

                    messages.append((time_text, author, msg, offset))
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

    out = "chatlog.csv"
    open(out, "w").close()
    total = 0
    max_seen_offset = 0
    seen_continuations = set()

    print("time,user,comment")
    with open(out, "a", encoding="utf-8") as f:
        f.write("time,user,comment\n")

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

        with open(out, "a", encoding="utf-8") as f:
            for t, author, msg, offset in msgs:
                total += 1
                print(f"{t},{author},{msg}", flush=True)
                f.write(f"{t},{author},{msg}\n")

        next_c = extract_next_cont(data)
        if not next_c:
            print("🟢 已无更多 continuation，已终止。")
            break
        continuation = next_c

        if i % 20 == 0:
            elapsed = int(time.time() - start_time)
            print(f"⏳ 已用时 {elapsed}s / 已获取 {total} 条 / 当前 {max_seen_offset//1000}s")

        time.sleep(0.08)

    print(f"✅ 完成：已将 {total} 条评论保存到 {out}。")

    # 🧹 删除重复评论处理（最后统一处理）
    try:
        with open(out, "r", encoding="utf-8") as f:
            lines = f.readlines()

        seen = set()
        unique_lines = []
        for line in lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)

        with open(out, "w", encoding="utf-8") as f:
            f.writelines(unique_lines)

        removed = len(lines) - len(unique_lines)
        if removed > 0:
            print(f"🧽 已删除 {removed} 行重复内容。")
    except Exception as e:
        print(f"⚠️ 删除重复内容时出错: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python youtubeChatdl.py <youtube_url>")
    else:
        main(sys.argv[1])
