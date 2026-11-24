# -*- coding: utf-8 -*-
"""
SoundShredder zh-CN —— 非官方中文界面补丁

原理
    不改动程序任何一行原有逻辑，只在三个页面的 </body> 前注入一段翻译脚本。
    脚本在页面渲染时替换英文文案，并用 MutationObserver 处理后续动态生成的
    文字（进度、状态、报错）。词条表单独放在 zh-CN.json，方便贡献翻译。

    本补丁只包含自己写的代码，不分发、不重打包 SoundShredder 的任何文件；
    它仅在你已经安装好的本地副本上做字符串替换。

用法
    python apply_zh.py                应用中文
    python apply_zh.py --check        查看当前状态
    python apply_zh.py --revert       还原英文
    python apply_zh.py --app "D:\\SoundShredder"   手动指定安装目录
    python apply_zh.py --terms other.json          使用自定义词条表

程序更新会覆盖页面文件，届时重新运行一次即可恢复中文。
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

MARK_START = "<!-- zh-cn:start (SoundShredder 中文补丁 · 用 apply_zh.py --revert 还原) -->"
MARK_END = "<!-- zh-cn:end -->"

# 兼容历史版本的标记文字：无论注释内容如何，整块剥离
BLOCK_RE = re.compile(r"<!--\s*zh-cn:start[^>]*?-->.*?<!--\s*zh-cn:end\s*-->", re.S)
ANY_MARK_RE = re.compile(r"<!--\s*zh-cn:start", re.I)

TARGETS = [
    ("static/index.html", "主界面"),
    ("static/lab.html", "混音台"),
    ("desktop/setup.html", "安装/设置页"),
]

JS_TEMPLATE = r"""
(function () {
  "use strict";
  var MAP = __DICT__;
  var ATTRS = ["placeholder", "title", "aria-label"];
  var SKIP = /^(SCRIPT|STYLE|TEXTAREA)$/;
  var RULES = [[/^(\d+:\d{2}(?::\d{2})?) elapsed$/, "$1 已用"]];

  function tr(value) {
    if (!value) return null;
    var key = value.trim();
    if (!key) return null;
    var out = MAP[key];
    if (typeof out === "string" && out) return out;
    for (var i = 0; i < RULES.length; i++) {
      if (RULES[i][0].test(key)) return key.replace(RULES[i][0], RULES[i][1]);
    }
    return null;
  }

  function fixText(node) {
    try {
      var raw = node.nodeValue;
      if (!raw) return;
      var out = tr(raw);
      if (out === null) return;
      var lead = (raw.match(/^\s*/) || [""])[0];
      var tail = (raw.match(/\s*$/) || [""])[0];
      var next = lead + out + tail;
      if (next !== raw) node.nodeValue = next;
    } catch (e) {}
  }

  function fixAttrs(el) {
    try {
      if (!el.getAttribute) return;
      for (var i = 0; i < ATTRS.length; i++) {
        var a = ATTRS[i];
        var val = el.getAttribute(a);
        if (!val) continue;
        var out = tr(val);
        if (out !== null && out !== val) el.setAttribute(a, out);
      }
    } catch (e) {}
  }

  function walk(root) {
    try {
      if (!root) return;
      if (root.nodeType === 3) { fixText(root); return; }
      if (root.nodeType !== 1) return;
      if (SKIP.test(root.tagName)) return;
      fixAttrs(root);
      var nested = root.querySelectorAll("*");
      for (var i = 0; i < nested.length; i++) {
        var el = nested[i];
        if (SKIP.test(el.tagName)) continue;
        fixAttrs(el);
        for (var c = el.firstChild; c; c = c.nextSibling) {
          if (c.nodeType === 3) fixText(c);
        }
      }
      for (var d = root.firstChild; d; d = d.nextSibling) {
        if (d.nodeType === 3) fixText(d);
      }
    } catch (e) {}
  }

  function fixTitle() {
    try {
      var out = tr(document.title);
      if (out) document.title = out;
    } catch (e) {}
  }

  function boot() {
    walk(document.body);
    fixTitle();
    setTimeout(function () { walk(document.body); fixTitle(); }, 250);
    setTimeout(function () { walk(document.body); }, 1200);
  }

  try { window.__zhTranslate = tr; } catch (e) {}

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }

  try {
    var mo = new MutationObserver(function (records) {
      for (var i = 0; i < records.length; i++) {
        var r = records[i];
        if (r.type === "characterData") {
          fixText(r.target);
        } else {
          for (var j = 0; j < r.addedNodes.length; j++) walk(r.addedNodes[j]);
        }
      }
    });
    mo.observe(document.documentElement, { childList: true, subtree: true, characterData: true });
  } catch (e) {}
})();
""".strip()


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def load_terms(custom):
    path = Path(custom).expanduser() if custom else script_dir() / "zh-CN.json"
    if not path.is_file():
        raise SystemExit(
            "找不到词条表：%s\n"
            "请把 zh-CN.json 和本脚本放在同一目录，或用 --terms 指定。" % path
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit("词条表格式错误（%s）：%s" % (path, exc))
    if not isinstance(data, dict):
        raise SystemExit("词条表必须是 {英文: 中文} 的对象。")
    return {str(k): str(v) for k, v in data.items() if k and v}


def candidate_roots():
    """按优先级列出可能的安装目录 / 存储目录。"""
    import os

    seen = set()
    queue = []

    def push(value):
        if not value:
            return
        key = str(value).lower()
        if key in seen:
            return
        seen.add(key)
        queue.append(value)

    env_home = os.environ.get("SOUNDSHREDDER_DESKTOP_HOME")
    if env_home:
        push(env_home)

    local = os.environ.get("LOCALAPPDATA")
    if local:
        cfg = Path(local) / "SoundShredder" / "desktop-storage.json"
        if cfg.is_file():
            try:
                home = json.loads(cfg.read_text(encoding="utf-8")).get("home")
                if isinstance(home, str) and home:
                    push(home)
            except Exception:
                pass
        push(str(Path(local) / "SoundShredder"))
        push(str(Path(local) / "Programs" / "SoundShredder"))

    here = script_dir()
    push(str(here))
    push(str(here / "SoundShredder"))
    push(str(here.parent))

    for drive in ("C:", "D:", "E:", "F:", "G:"):
        push(drive + "\\SoundShredder")
        push(drive + "\\Audio tools\\SoundShredder")

    roots = []
    for item in queue:
        base = Path(item).expanduser()
        roots.extend([base / "app" / "resources" / "backend", base / "resources" / "backend", base])
    return roots


def backend_root(explicit):
    if explicit:
        base = Path(explicit).expanduser()
        for candidate in (base / "app" / "resources" / "backend", base / "resources" / "backend", base):
            if (candidate / "static" / "index.html").is_file():
                return candidate
        raise SystemExit("指定目录里没找到 SoundShredder：%s" % base)

    for candidate in candidate_roots():
        if (candidate / "static" / "index.html").is_file():
            return candidate

    raise SystemExit(
        "没找到 SoundShredder 安装目录。\n"
        "请用 --app 手动指定，例如：\n"
        "  python apply_zh.py --app \"D:\\SoundShredder\"\n"
        "  python apply_zh.py --app \"%LOCALAPPDATA%\\Programs\\SoundShredder\""
    )


def build_block(terms):
    payload = json.dumps(terms, ensure_ascii=False, indent=0)
    js = JS_TEMPLATE.replace("__DICT__", payload)
    return MARK_START + "\n<script>\n" + js + "\n</script>\n" + MARK_END + "\n"


def strip_block(text):
    """剥离任意版本注入块，保证重复运行不会叠加。"""
    previous = None
    while previous != text:
        previous = text
        text = BLOCK_RE.sub("", text)
    # 兜底：只剩起始标记没有结束标记的残缺块
    while ANY_MARK_RE.search(text):
        start = ANY_MARK_RE.search(text).start()
        text = text[:start]
    return text.strip("\r\n") + "\n" if text.strip() else text


def apply(backend, terms):
    block = build_block(terms)
    changed = 0
    for rel, label in TARGETS:
        path = backend / rel
        if not path.is_file():
            print("  [跳过] %-22s 不存在" % rel)
            continue
        backup = path.with_suffix(path.suffix + ".en.bak")
        raw = path.read_text(encoding="utf-8", newline="")
        if not backup.exists():
            shutil.copy2(path, backup)
        body = strip_block(raw)
        if "</body>" not in body:
            print("  [跳过] %-22s 结构异常，未找到 </body>" % rel)
            continue
        new = body.replace("</body>", block + "</body>", 1)
        if new != raw:
            path.write_text(new, encoding="utf-8", newline="")
            changed += 1
            print("  [完成] %-22s %s" % (rel, label))
        else:
            print("  [原样] %-22s 已是中文版" % rel)
    return changed


def revert(backend):
    for rel, label in TARGETS:
        path = backend / rel
        backup = path.with_suffix(path.suffix + ".en.bak")
        if backup.is_file():
            shutil.copy2(backup, path)
            print("  [还原] %-22s %s" % (rel, label))
        elif path.is_file():
            path.write_text(strip_block(path.read_text(encoding="utf-8", newline="")), encoding="utf-8", newline="")
            print("  [还原] %-22s 已移除注入块" % rel)


def check(backend):
    for rel, _label in TARGETS:
        path = backend / rel
        if not path.is_file():
            print("  %-22s 缺失" % rel)
            continue
        text = path.read_text(encoding="utf-8", newline="")
        blocks = len(BLOCK_RE.findall(text))
        state = "中文版" if blocks == 1 else ("中文版(重复 %d 块)" % blocks if blocks > 1 else "英文原版")
        backup = "有备份" if path.with_suffix(path.suffix + ".en.bak").is_file() else "无备份"
        print("  %-22s %-8s %s" % (rel, state, backup))


def main():
    parser = argparse.ArgumentParser(description="SoundShredder 非官方中文界面补丁")
    parser.add_argument("--revert", action="store_true", help="还原成英文")
    parser.add_argument("--check", action="store_true", help="查看当前状态")
    parser.add_argument("--app", metavar="DIR", help="手动指定 SoundShredder 安装目录")
    parser.add_argument("--terms", metavar="FILE", help="使用自定义词条表（默认 zh-CN.json）")
    args = parser.parse_args()

    backend = backend_root(args.app)
    print("程序目录：%s" % backend)

    if args.check:
        check(backend)
        return 0

    if args.revert:
        revert(backend)
        print("\n已还原英文。重新打开 SoundShredder 生效。")
        return 0

    terms = load_terms(args.terms)
    print("词条数：%d" % len(terms))
    print("\n开始应用中文补丁：")
    changed = apply(backend, terms)
    print("\n完成，共更新 %d 个页面。重启 SoundShredder 后生效。" % changed)
    if changed:
        print("程序更新后界面变回英文时，重新运行本脚本即可。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
