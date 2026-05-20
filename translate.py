#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =========================================
# Ollila Translator Complete Edition v2
# MeCab + 文法エンジン + Modifier対応
# =========================================

import json
import os
import MeCab

# =========================================
# 設定
# =========================================

DICT_FILE = "dictionary.json"

# =========================================
# デフォルト辞書
# =========================================

default_dict = {

    # 名詞
    "私": "dii",
    "あなた": "mism",
    "人": "hmaon",
    "村": "ollcco",
    "本": "oiiauq",
    "記録": "assylpl",
    "記憶": "azciia",
    "言語": "yallq",
    "辞書": "llaecoayos",
    "水": "lloy",

    # 動詞
    "見る": "ollo",
    "書く": "suqoy",
    "残す": "rem",
    "無くす": "oyaq",
    "飲む": "llqyawo",
    "生きる": "scollog",

    # その他
    "この": "qpella",
    "もし": "sces",
    "そして": "ete",
    "ため": "dor",

    # 助詞
    "__TOPIC__": "lle",
    "__LOCATION__": "des",
}

# =========================================
# 辞書ロード
# =========================================

if os.path.exists(DICT_FILE):

    try:

        with open(DICT_FILE, "r", encoding="utf-8") as f:
            jp_to_lang = json.load(f)

    except json.JSONDecodeError:

        print("dictionary.json が壊れています")
        print("デフォルト辞書を復元します")

        jp_to_lang = default_dict

else:

    jp_to_lang = default_dict

# 不足キー補完
for k, v in default_dict.items():

    if k not in jp_to_lang:
        jp_to_lang[k] = v

# 保存
with open(DICT_FILE, "w", encoding="utf-8") as f:
    json.dump(jp_to_lang, f, ensure_ascii=False, indent=4)

# =========================================
# 保存
# =========================================

def save_dict():

    with open(DICT_FILE, "w", encoding="utf-8") as f:
        json.dump(jp_to_lang, f, ensure_ascii=False, indent=4)

# =========================================
# 逆辞書
# =========================================

def rebuild_reverse():
    return {v: k for k, v in jp_to_lang.items()}

lang_to_jp = rebuild_reverse()

# =========================================
# 未知語学習
# =========================================

def learn_word(word):

    print(f"\n未知語検出: {word}")

    translated = input("Ollila語を入力 > ")

    jp_to_lang[word] = translated

    save_dict()

    global lang_to_jp
    lang_to_jp = rebuild_reverse()

    print(f"{word} -> {translated} を保存しました")

# =========================================
# 単語取得
# =========================================

def get_word(word):

    if word not in jp_to_lang:
        learn_word(word)

    return jp_to_lang[word]

# =========================================
# MeCab
# =========================================

try:

    tagger = MeCab.Tagger("-r /etc/mecabrc")

except RuntimeError:

    print("MeCab 初期化失敗")
    print("/etc/mecabrc を確認してください")

    exit()

# =========================================
# 日本語解析
# =========================================

def parse_japanese(text):

    node = tagger.parseToNode(text)

    parsed = {
        "subject": None,
        "object": None,
        "location": None,
        "verb": None,
        "purpose": None,
        "extra_verbs": [],
        "raw": [],
        "topic": False,
    }

    pending_word = None
    verbs = []
    last_verb = None

    while node:

        word = node.surface
        features = node.feature.split(",")

        pos = features[0]

        base = word

        # 原形取得
        if len(features) >= 7:

            if features[6] != "*":
                base = features[6]

        # =====================================
        # 助詞
        # =====================================

        if word == "は":

            parsed["subject"] = pending_word
            parsed["topic"] = True

            pending_word = None

        elif word == "を":

            parsed["object"] = pending_word

            pending_word = None

        elif word == "で":

            parsed["location"] = pending_word

            pending_word = None

        elif word == "に":

            if pending_word:
                parsed["raw"].append(pending_word)

            pending_word = None

        # =====================================
        # modifier : ため
        # =====================================

        elif base == "ため":

            if last_verb:

                parsed["purpose"] = last_verb

                if last_verb in verbs:
                    verbs.remove(last_verb)

        # =====================================
        # 動詞
        # =====================================

        elif pos == "動詞":

            verbs.append(base)

            last_verb = base

        # =====================================
        # 名詞など
        # =====================================

        elif pos in ["名詞", "形容詞", "副詞"]:

            pending_word = base

        node = node.next

    # 残り語
    if pending_word:
        parsed["raw"].append(pending_word)

    # 最後の動詞を主動詞
    if verbs:

        parsed["verb"] = verbs[-1]

        if len(verbs) > 1:
            parsed["extra_verbs"] = verbs[:-1]

    return parsed

# =========================================
# Ollila生成
# =========================================

def generate_ollila(parsed):

    parts = []

    # 主語
    if parsed["subject"]:

        parts.append(get_word(parsed["subject"]))

        if parsed["topic"]:
            parts.append(get_word("__TOPIC__"))

    # purpose
    if parsed["purpose"]:

        parts.append(get_word(parsed["purpose"]))
        parts.append(get_word("ため"))

    # raw
    for word in parsed["raw"]:

        parts.append(get_word(word))

    # 場所
    if parsed["location"]:

        parts.append(get_word(parsed["location"]))
        parts.append(get_word("__LOCATION__"))

    # 目的語
    if parsed["object"]:

        parts.append(get_word(parsed["object"]))

    # extra verbs
    for v in parsed["extra_verbs"]:

        parts.append(get_word(v))

    # 主動詞
    if parsed["verb"]:

        parts.append(get_word(parsed["verb"]))

    return " ".join(parts)

# =========================================
# 日本語 → Ollila
# =========================================

def translate_jp_to_ollila(text):

    parsed = parse_japanese(text)

    print("\n[Parser結果]")
    print(parsed)

    result = generate_ollila(parsed)

    return result

# =========================================
# Ollila → 日本語
# =========================================

def translate_ollila_to_jp(text):

    words = text.split()

    result = []

    for word in words:

        if word in lang_to_jp:

            jp = lang_to_jp[word]

            # 内部記号は非表示
            if jp.startswith("__"):
                continue

            result.append(jp)

        else:

            result.append(f"[{word}]")

    return " ".join(result)

# =========================================
# CLI
# =========================================

def main():

    print("===================================")
    print("   Ollila Translator Complete")
    print("===================================")

    while True:

        print("\n1 : 日本語 → Ollila")
        print("2 : Ollila → 日本語")
        print("0 : 終了")

        mode = input(">>> ")

        # 終了
        if mode == "0":

            print("終了します")
            break

        # 日本語 → Ollila
        elif mode == "1":

            text = input("\n日本語入力:\n> ")

            result = translate_jp_to_ollila(text)

            print("\n翻訳結果:")
            print(result)

        # Ollila → 日本語
        elif mode == "2":

            text = input("\nOllila入力:\n> ")

            result = translate_ollila_to_jp(text)

            print("\n翻訳結果:")
            print(result)

        else:

            print("無効な入力")

# =========================================

if __name__ == "__main__":
    main()
