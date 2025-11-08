"""YouTube 聊天回放获取核心模块"""

import re
import json
import time
import requests
from yt_dlp import YoutubeDL
from tqdm import tqdm

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"


def fetch_html(url):
    """获取页面HTML"""
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.text


def extract_params(html):
    """从HTML中提取API参数"""
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
    """查找初始continuation token"""
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
    """获取聊天数据"""
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
            tqdm.write(f"⚠️ {type(e).__name__}: {e} — 重试 {attempt+1}/{retries}")
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

                    author_id = r.get("authorExternalChannelId", "")

                    msg_runs = r.get("message", {}).get("runs", [])
                    msg = "".join([x.get("text", "") for x in msg_runs]).strip()
                    if not msg:
                        continue

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

                    msg = re.sub(r"[\x00-\x1F\x7F]", "", msg)

                    messages.append({
                        "time_text": time_text,
                        "author": author,
                        "author_id": author_id,
                        "message": msg,
                        "offset_ms": offset
                    })
                    if offset > latest_offset:
                        latest_offset = offset
    return messages, latest_offset


def extract_next_cont(json_data):
    """提取下一个continuation token"""
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


def get_video_info(url, cookies_file=None):
    """获取视频信息"""
    ydl_opts = {}
    if cookies_file:
        ydl_opts['cookiefile'] = cookies_file
    
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "id": info.get("id", "unknown"),
            "title": info.get("title", ""),
            "duration": info.get("duration", 0),
            "upload_date": info.get("upload_date", ""),
            "url": url
        }


def get_livestream_urls(channel_url, cookies_file=None):
    """获取频道的所有直播视频链接"""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'no_warnings': True,
    }
    if cookies_file:
        ydl_opts['cookiefile'] = cookies_file
    
    urls = []
    with YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(channel_url, download=False)
            if result and 'entries' in result:
                for entry in result['entries']:
                    if entry and entry.get('live_status') == 'was_live':
                        video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                        urls.append(video_url)
        except Exception as e:
            print(f"❌ 获取频道视频列表失败: {e}")
    
    return urls


def fetch_video_chat(url, cookies_file=None, verbose=True):
    """获取单个视频的聊天回放数据"""
    if verbose:
        print(f"▶ Fetching: {url}")
    
    video_info = get_video_info(url, cookies_file)
    duration = video_info["duration"]
    video_id = video_info["id"]
    
    if verbose:
        print(f"📏 视频长度: {duration} 秒")

    html = fetch_html(url)
    api_key, version, yid = extract_params(html)
    if not yid:
        print("❌ 未找到 ytInitialData。可能需要 Cookie。")
        return None

    continuation = find_continuation(yid)
    if not continuation:
        print("❌ 未找到 continuation。")
        return None

    all_messages = []
    max_seen_offset = 0
    seen_continuations = set()

    pbar = None
    if verbose:
        pbar = tqdm(total=duration, unit='s', desc='下载进度', bar_format='{desc}: {percentage:3.0f}%|{bar}| {n:.0f}/{total:.0f}s [{elapsed}<{remaining}]')

    start_time = time.time()
    for i in range(3000):
        if continuation in seen_continuations:
            if pbar:
                pbar.close()
            break
        seen_continuations.add(continuation)

        data = fetch_chat(api_key, version, continuation)
        actions = data.get("actions") or data.get("continuationContents", {}).get(
            "liveChatContinuation", {}
        ).get("actions")
        msgs, latest_offset = parse_messages(actions)

        if latest_offset > max_seen_offset:
            max_seen_offset = latest_offset
            if pbar:
                pbar.n = min(max_seen_offset / 1000, duration)
                pbar.refresh()

        if max_seen_offset / 1000 >= duration:
            if pbar:
                pbar.n = duration
                pbar.refresh()
                pbar.close()
            break

        all_messages.extend(msgs)

        next_c = extract_next_cont(data)
        if not next_c:
            if pbar:
                pbar.close()
            break
        continuation = next_c

        time.sleep(0.08)

    if pbar and not pbar.disable:
        pbar.close()

    if verbose:
        print(f"✅ 完成：已获取 {len(all_messages)} 条评论")

    return {
        "video_info": video_info,
        "messages": all_messages,
        "statistics": {
            "total_messages": len(all_messages),
            "unique_authors": len(set(m["author_id"] for m in all_messages if m["author_id"])),
            "time_range": {
                "min": ms_to_timestamp(min((m["offset_ms"] for m in all_messages), default=0)),
                "max": ms_to_timestamp(max((m["offset_ms"] for m in all_messages), default=0))
            }
        }
    }
