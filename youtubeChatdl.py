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
            print(f"⚠️ {type(e).__name__}: {e} — 再試行 {attempt+1}/{retries}")
            time.sleep(3)
    raise RuntimeError("❌ 再試行しても取得できませんでした。")


def ms_to_timestamp(ms):
    """ミリ秒を 0:00 形式に変換"""
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

                    # タイムスタンプ取得（負の時間は完全スキップ）
                    offset = 0
                    time_text = "0:00"
                    if "videoOffsetTimeMsec" in r:
                        try:
                            offset = int(float(r["videoOffsetTimeMsec"]))
                            if offset < 0:
                                continue  # 🧹 負の時間コメント除外
                            time_text = ms_to_timestamp(offset)
                        except:
                            pass
                    elif "timestampText" in r:
                        time_text = r["timestampText"].get("simpleText", "0:00").strip()
                        if time_text.startswith(
                            "-"
                        ):  # ✅ マイナス表記を検出してスキップ
                            continue

                    # 不正文字除去
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
    # 🎬 動画情報を取得（duration秒を取得）
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        duration = info.get("duration", 0)
    print(f"📏 動画の長さ: {duration} 秒")

    html = fetch_html(url)
    api_key, version, yid = extract_params(html)
    if not yid:
        print("❌ ytInitialData が見つかりません。Cookie が必要かも。")
        return

    continuation = find_continuation(yid)
    if not continuation:
        print("❌ continuation が見つかりません。")
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
            print("🔁 同じ continuation が繰り返されたため終了します。")
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
            print(f"🏁 動画時間（{duration}s）に到達したため終了します。")
            break

        with open(out, "a", encoding="utf-8") as f:
            for t, author, msg, offset in msgs:
                total += 1
                print(f"{t},{author},{msg}", flush=True)
                f.write(f"{t},{author},{msg}\n")

        next_c = extract_next_cont(data)
        if not next_c:
            print("🟢 continuation が無くなったため終了します。")
            break
        continuation = next_c

        if i % 20 == 0:
            elapsed = int(time.time() - start_time)
            print(f"⏳ {elapsed}s経過 / {total}件取得 / 現在 {max_seen_offset//1000}s")

        time.sleep(0.08)

    print(f"✅ 完了: {total} 件のコメントを {out} に保存しました。")

    # 🧹 重複コメント削除処理（最後にまとめて）
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
            print(f"🧽 重複 {removed} 行を削除しました。")
    except Exception as e:
        print(f"⚠️ 重複削除中にエラー: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python youtubeChatdl.py <youtube_url>")
    else:
        main(sys.argv[1])