# -*- coding: utf-8 -*-
"""小説解説ビデオの台本（scenario.json）の文末を数える。聞きやすさの確認用。

使い方:
    python scripts/novel_check_endings.py <動画ページのフォルダ> [...]

出力: 文末の分布、過去形の割合、同じ文末が3文続く箇所（体言止め・常体は4文続く箇所）、「でした」2回以上・「のです」3回以上の場面。
基準は _AIDIY/knowledge/frontend_web,X系小説解説ビデオ作成手順.md の「文末（聞きやすさ）」。
「常体/体言」は「〜る。」「〜ない。」や体言止めの文。1場面の long では、全体の4割程度までを目安にする。
"""
import collections
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

PAST = re.compile(r"(でした|ました|だった|ていた|いた|った|んだ|した|れた|えた|けた|めた|た)[」』）)]*$")
SPLIT = re.compile(r"(?<=[。！？])")


def sentences(text):
    return [s for s in SPLIT.split(text) if s.strip()]


def group(sentence):
    s = sentence.strip().rstrip("。！？")
    if re.search(r"(のです|のでした)$", s):
        return "のです"
    if s.endswith("でした"):
        return "でした"
    if PAST.search(s):
        return "過去"
    if re.search(r"ません$", s):
        return "ません"
    if re.search(r"(でいます|ています)$", s):
        return "ています"
    if re.search(r"ます$", s):
        return "ます"
    if re.search(r"(です|でしょう)$", s):
        return "です"
    return "常体/体言"


def check(folder):
    data = json.load(open(os.path.join(folder, "scenario.json"), encoding="utf-8-sig"))
    print("==", data.get("title", folder))
    total = {"short": collections.Counter(), "long": collections.Counter()}
    problems = []
    for scene in data["scenes"]:
        for kind in ("short", "long"):
            groups = [group(s) for s in sentences(scene[f"{kind}_narration"])]
            total[kind].update(groups)
            run = 1
            for i in range(1, len(groups)):
                run = run + 1 if groups[i] == groups[i - 1] else 1
                limit = 4 if groups[i] == "常体/体言" else 3   # 体言止め・常体は畳みかけに使えるので3文まで許す
                if run == limit:
                    problems.append(f"{scene['id']} {kind}: 「{groups[i]}」が{limit}文続く（{i + 1}文目まで）")
            if kind == "long":
                count = collections.Counter(groups)
                if count["でした"] > 1:
                    problems.append(f"{scene['id']} long: 「でした」が{count['でした']}回")
                if count["のです"] > 2:
                    problems.append(f"{scene['id']} long: 「のです」が{count['のです']}回")
    for kind in ("long", "short"):
        n = sum(total[kind].values()) or 1
        print(f"{kind}: {dict(total[kind])}  過去形 {sum(v for k, v in total[kind].items() if k in ('過去', 'でした'))}/{n}文")
    print("問題なし" if not problems else "\n".join(problems))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for folder in sys.argv[1:]:
        check(folder)
