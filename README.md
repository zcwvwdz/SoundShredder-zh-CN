# SoundShredder 中文界面补丁

非官方简体中文翻译 · Unofficial Simplified Chinese UI patch for [SoundShredder](https://github.com/xD4O/SoundShredder)

> **双击 `apply-zh.cmd` 即可，不需要安装 Python，不改动程序逻辑，随时一键还原。**
> Double-click `apply-zh.cmd`. No Python install needed, no logic touched, fully reversible.

---

## 这是什么

SoundShredder 目前只有英文界面，作者没有做多语言支持。这个项目用**注入式翻译**补上中文：

- 在三个页面的 `</body>` 前插入一段翻译脚本，页面渲染时把英文文案换成中文
- 用 `MutationObserver` 监听后续动态生成的文字，所以进度提示、状态、报错也会变中文
- **程序原有 JS 逻辑一行未改**，随时可以完整还原

| 已汉化 | 未汉化 |
|---|---|
| 主界面（导入、预设、三轨滑块、导出） | Electron 菜单栏（SoundShredder / Help） |
| 混音台 Mixing Lab（推子、时间编辑、导出） | 更新弹窗、系统文件对话框 |
| 安装 / 设置页 | 品牌名（cyr4x、Higgsfield Community） |
| 状态提示、错误信息、按钮 tooltip | 纯数字格式（如 `0.000 – 1.000 s`） |

共 **336 条词条**，页面静态文案覆盖率约 98%。

---

## 安装

### Windows（桌面版）

1. 下载本仓库（右上角 `Code → Download ZIP`），或从 [Releases](../../releases) 下载 zip
2. 解压到任意目录（不要解压到 `C:\Program Files` 之类需要管理员权限的位置）
3. 双击 **`apply-zh.cmd`**
4. 重启 SoundShredder，界面即为中文

启动器会自动找到你的安装目录和程序自带的 Python。如果提示找不到，可以指定路径：

```bat
apply-zh.cmd --app "D:\SoundShredder"
```

### 手动运行（任意平台）

```bash
python apply_zh.py                                  # 自动探测安装目录
python apply_zh.py --app "D:\SoundShredder"         # 手动指定
python apply_zh.py --check                          # 查看当前状态
python apply_zh.py --revert                         # 还原英文
```

> macOS / Linux 版理论上可用（`python3 apply_zh.py`），但**未测试**，路径也需要用 `--app` 指定。

---

## 还原与更新

| 场景 | 操作 |
|---|---|
| 想变回英文 | `apply-zh.cmd --revert` |
| SoundShredder 更新后变回英文 | 重新运行 `apply-zh.cmd` |
| 查看当前状态 | `apply-zh.cmd --check` |

原文件会备份为 `*.en.bak`，`--revert` 直接用它覆盖回去。

---

## 原理

```
backend/static/index.html      ← </body> 前注入 <script>
backend/static/lab.html        ← 同上
backend/desktop/setup.html     ← 同上
backend/static/zh-CN.json      ← 词条表（不在安装目录，本仓库自带）
```

注入的脚本做四件事：

1. 遍历 DOM，把文本节点与 `placeholder` / `title` / `aria-label` 属性按词条表替换
2. 替换 `document.title`
3. 监听 `MutationObserver`，处理 JS 后续生成的文字
4. 首次替换后延时补扫两次，覆盖晚加载的区域

安全性：已确认 `app.js` / `lab.js` 中**没有**基于 `textContent` 的逻辑判断，也没有按界面文字选择元素的代码，因此替换文案不会影响任何功能。所有替换都包在 `try/catch` 里，出错最多是保持英文，不会白屏。

重复运行是幂等的：脚本会先剥离已有的注入块再插入，不会叠加。

---

## 贡献翻译

词条在 [`zh-CN.json`](zh-CN.json)，格式就是 `{"英文原文": "中文译文"}`：

```json
{
  "Separate audio": "开始分离",
  "Bubble FX": "气泡清理"
}
```

欢迎提 PR 补充词条或修改不贴切的译法。注意两点：

- 键必须与界面英文**完全一致**（区分大小写，注意 `’`、`·`、`→` 这类字符）
- 按钮文案尽量简短，太长会挤破布局

想添加其他语言，复制一份 `zh-CN.json` 改名为 `xx-XX.json`，用 `--terms xx-XX.json` 加载即可。

---

## 已验证

- SoundShredder **1.3.0**（Windows x64 桌面版）
- Windows 10 22H2，RTX 5060
- 主界面 / 混音台 / 安装页均显示正常，无布局错位

---

## 免责声明

本项目为**第三方非官方**补丁，与 SoundShredder 作者 cyr4x 无关，未获其授权或背书。

上游仓库目前**未提供 LICENSE**（默认保留所有权利）。因此本仓库**只包含本人编写的脚本与词条表**，不包含、不分发、不重新打包 SoundShredder 的任何文件或资源；补丁仅作用于你本机已合法安装的副本，效果等同于手动修改本机文件。

如果作者希望把这个翻译合并到上游，我很乐意改写成正式的 i18n 方案提交 PR。

---

## License

本仓库的代码与词条表采用 [MIT](LICENSE)。SoundShredder 本身版权归其作者所有，不在本许可范围内。
