"""
全コミットの diff 内容から 1日毎の要約文を生成。
git -c core.quotepath=false で日本語ファイル名を正しく扱う。
"""
import subprocess, os, sys, re
from collections import defaultdict, Counter
from datetime import datetime

HISTORIES = os.path.join(os.path.dirname(__file__), "histories")
TMP = os.path.join(os.path.dirname(__file__), "_tmp_clone")

GIT = 'git -c core.quotepath=false'

def run(cmd, cwd=TMP):
    return subprocess.run(
        cmd, shell=True, capture_output=True, text=True, cwd=cwd,
        encoding="utf-8", errors="replace",
    )

# 全コミット取得
r = run(f'{GIT} log --reverse --format="%H|%ai|%s"')
if r.returncode != 0:
    print("ERROR:", r.stderr); sys.exit(1)

commits = []
for line in r.stdout.strip().split("\n"):
    if not line: continue
    try: sha, date_str, subject = line.split("|", 2)
    except ValueError: continue
    commits.append((sha, date_str, subject))

print(f"Total commits: {len(commits)}")

def get_files(sha):
    """1コミットの変更ファイル一覧 [(status, path), ...]"""
    r = run(f'{GIT} diff-tree --no-commit-id --name-status -r "{sha}"')
    files = []
    if r.returncode != 0: return files
    for line in r.stdout.strip().split("\n"):
        if not line: continue
        parts = line.split("\t")
        if len(parts) >= 2:
            files.append((parts[0], parts[1]))
    return files

def get_diff_head(sha, max_lines=40):
    """diff の先頭部分を取得"""
    r = run(f'{GIT} show --format="" --no-color "{sha}"')
    if r.returncode != 0: return ""
    lines = r.stdout.split("\n")[:max_lines]
    return "\n".join(lines)

# ── 1日分の要約生成 ──
def day_summary_and_changes(date_key, day_commits):
    """
    1日分の変更を分析し、(要約文, コミット詳細行リスト) を返す。
    """
    # 全日のファイルを収集
    all_files = []
    commit_details = []  # (time, sha, msg, file_list, diff_head)

    for dt, sha, subject in day_commits:
        files = get_files(sha)
        all_files.extend(files)
        diff_head = get_diff_head(sha)
        commit_details.append((dt, sha, subject, files, diff_head))

    if not all_files:
        return "（変更内容なし）", commit_details

    # ── カテゴリ集計 ──
    cat_count = Counter()
    top_dirs = Counter()
    feature_names = set()

    for status, p in all_files:
        parts = p.replace("\\", "/").split("/")
        top = parts[0]
        top_dirs[top] += 1
        # カテゴリ判定
        if top == "backend_server":
            cat_count["Backend"] += 1
            for part in parts:
                if re.match(r'^[CMTVSX]', part):
                    feature_names.add(part)
                if part == "AIコア": feature_names.add("AIコア")
        elif top == "backend_mcp":
            cat_count["MCP"] += 1
            for part in parts:
                if part.startswith("mcp_"): feature_names.add(part)
        elif top == "backend_hermes":
            cat_count["Hermes"] += 1
        elif top == "frontend_web":
            cat_count["Frontend Web"] += 1
            for part in parts:
                if re.match(r'^[CMTVSX]', part): feature_names.add(part)
        elif top == "frontend_avatar":
            cat_count["Frontend Avatar"] += 1
            for part in parts:
                if part in ("electron", "Electron"): feature_names.add("Electron")
                if "VRM" in part: feature_names.add("VRM")
        elif top == ".aidiy":
            cat_count["ナレッジ"] += 1
        elif top.startswith("_"):
            cat_count["スクリプト"] += 1
            feature_names.add(top)
        elif top in ("AGENTS.md", "CLAUDE.md", "README.md", "_AIDIY.md",
                      "LICENSE", "CONTRIBUTING.md", "NOTICE.md"):
            cat_count["ドキュメント"] += 1
        elif top == "docs":
            cat_count["ドキュメント"] += 1
        elif top in (".gitignore", ".gitattributes"):
            cat_count["設定"] += 1
        elif top in ("docker", "Docker"):
            cat_count["Docker"] += 1
        else:
            cat_count["その他"] += 1

    # ── diff 内容からの意図推測 ──
    all_diffs = "\n".join(d[4] for d in commit_details if d[4])
    n_add_files = sum(1 for s, _ in all_files if s == "A")
    n_del_files = sum(1 for s, _ in all_files if s == "D")
    total_files = len(all_files)

    # 要約文の構成
    parts = []

    # 新規追加の規模
    if n_add_files >= 20:
        parts.append(f"新規ファイル大量追加（+{n_add_files}）")
    elif n_add_files >= 5:
        parts.append(f"新規ファイル追加（+{n_add_files}）")

    # 削除の規模
    if n_del_files >= 20:
        parts.append(f"ファイル大量削除（-{n_del_files}）")
    elif n_del_files >= 5:
        parts.append(f"不要ファイル削除（-{n_del_files}）")

    # モジュール名から機能を推測
    if feature_names:
        f_list = sorted(feature_names)
        kw = "、".join(f_list[:3])
        if len(f_list) > 3: kw += "など"
        parts.append(f"{kw}を修正")

    # 主要カテゴリ
    top_cats = [c for c, _ in cat_count.most_common(2)]
    if not feature_names:
        parts.append(f"{'・'.join(top_cats)}の更新")

    # diff 内容からキーワード検出
    diff_keywords = []
    for kw, label in [
        ("WebSocket", "WebSocket"), ("websocket", "WebSocket"),
        ("JWT", "JWT"), ("jwt", "JWT"), ("認証", "認証"),
        ("VRM", "VRM"), ("Three.js", "Three.js"),
        ("Electron", "Electron"), ("electron", "Electron"),
        ("ffmpeg", "ffmpeg"), ("FFmpeg", "ffmpeg"),
        ("OBS", "OBS"), ("obs", "OBS"),
        ("TTS", "TTS"), ("tts", "TTS"),
        ("Monaco", "Monaco Editor"), ("monaco", "Monaco Editor"),
        ("proxy", "proxy"), ("Proxy", "proxy"),
        ("Docker", "Docker"), ("docker", "Docker"),
        ("nginx", "nginx"), ("Nginx", "Nginx"),
        ("sqlite", "SQLite"), ("SQLite", "SQLite"),
        ("PostgreSQL", "PostgreSQL"), ("postgres", "PostgreSQL"),
        ("uvicorn", "uvicorn"), ("FastAPI", "FastAPI"),
    ]:
        if kw in all_diffs:
            diff_keywords.append(label)
    if diff_keywords:
        unique = list(dict.fromkeys(diff_keywords))[:3]
        parts.append("・".join(unique) + "周りの変更")

    if not parts:
        parts.append(f"{'・'.join(top_cats)}の軽微な更新")

    summary = "、".join(parts[:3])
    if total_files >= 50:
        summary = "全体整備：" + summary
    summary += f"（{total_files}ファイル）"

    return summary, commit_details

# ── 実行 ──
by_date = defaultdict(list)
for sha, date_str, subject in commits:
    dt = datetime.fromisoformat(date_str)
    date_key = dt.strftime("%Y%m%d")
    by_date[date_key].append((dt, sha, subject))

# 既存ファイル削除
for f in os.listdir(HISTORIES):
    if f.endswith(".md"):
        os.remove(os.path.join(HISTORIES, f))

# 日付ごとに生成
for i, date_key in enumerate(sorted(by_date)):
    items = by_date[date_key]
    summary, cds = day_summary_and_changes(date_key, items)

    lines = []
    lines.append(f"# {date_key[:4]}-{date_key[4:6]}-{date_key[6:8]}")
    lines.append("")
    lines.append(f"> {summary}")
    lines.append("")

    for dt, sha, msg, files, _ in cds:
        short = sha[:7]
        time_str = dt.strftime("%H:%M")
        prefix = f"- [{time_str}] `{short}`"

        # コミットメッセージ（"backup" 以外は表示）
        if msg and msg != "backup":
            prefix += f" **{msg}**"

        if not files:
            lines.append(prefix)
            continue

        # ファイル名を整形（ディレクトリ階層を簡略化）
        simplified = []
        for st, p in files[:12]:
            base = os.path.basename(p)
            if st == "A": base = f"+{base}"
            elif st == "D": base = f"-{base}"
            simplified.append(base)
        detail = ", ".join(simplified)
        if len(files) > 12:
            detail += f" 他{len(files)-12}件"
        lines.append(f"{prefix} — {detail}")

    lines.append("")
    path = os.path.join(HISTORIES, f"{date_key}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    if (i+1) % 15 == 0:
        print(f"  {i+1}/{len(by_date)} done...")

print(f"\nDone: {len(by_date)} files -> .aidiy/histories/")
