# LOL 双向翻译悬浮窗

这是一个 Windows 上用于《英雄联盟》的独立桌面悬浮窗工具。它不注入 LOL 进程，不修改游戏文件，只通过置顶窗口、剪贴板和全局快捷键工作。

## 功能

- 英文/德文聊天内容翻译成中文
- 中文一键翻译成自然的游戏英语
- 中文转英文后默认直接复制，方便切回 LOL 后 `Ctrl+V` 发送
- 任意翻译结果都可以点“复制结果”直接复制
- 悬浮窗置顶显示
- 全局快捷键呼出/隐藏窗口
- 翻译服务接口可配置，当前优先支持 OpenAI API，并预留 DeepL

## 快捷键

默认快捷键：

- `Ctrl + Alt + T`：显示/隐藏悬浮窗
- `Ctrl + Alt + C`：读取剪贴板内容并翻译成中文
- `Ctrl + Alt + E`：把输入框里的中文翻译成英文并复制

如果快捷键无法使用，请用管理员身份运行终端或应用。Windows 上全局快捷键有时会被系统权限或其他软件拦截。

## 安装

需要 Python 3.10 或更新版本。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

然后编辑 `.env`，填入：

```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

## 运行

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

## 使用方式

翻译别人发的英文或德文：

1. 在 LOL 或聊天窗口里复制文字
2. 按 `Ctrl + Alt + C`
3. 悬浮窗显示中文翻译

把自己要说的中文翻成英文：

1. 按 `Ctrl + Alt + T` 打开悬浮窗
2. 输入中文，例如“等我大招再打龙”
3. 点击“中文译成英文并复制”，或按 `Ctrl + Alt + E`
4. 切回 LOL，按 `Ctrl + V` 发送

默认情况下，英文结果会自动进入剪贴板；不需要再手动选中文字复制。

## 配置

首次运行后会创建：

```text
%USERPROFILE%\.lol_translate_overlay\config.json
```

可以修改里面的快捷键和翻译服务：

```json
{
  "provider": "openai",
  "openai_model": "gpt-4o-mini",
  "deepl_target_lang": "ZH",
  "auto_copy_english": true,
  "auto_copy_clipboard_translation": false,
  "hotkey_toggle": "ctrl+alt+t",
  "hotkey_clipboard_to_chinese": "ctrl+alt+c",
  "hotkey_chinese_to_english": "ctrl+alt+e"
}
```

## GitHub 推送

如果已经安装 Git for Windows，可以直接双击项目里的：

```text
push_to_github.bat
```

第一次推送时，Git 可能会弹出 GitHub 登录窗口。登录完成后，如果第一次没有推成功，再双击运行一次即可。

如果你已经安装并登录 GitHub CLI，可以这样创建仓库并推送：

```powershell
git init
git add .
git commit -m "Initial LOL translate overlay"
gh repo create lol-translate-overlay --public --source . --remote origin --push
```

如果不用 GitHub CLI，也可以在 GitHub 网页新建一个空仓库，然后执行：

```powershell
git init
git add .
git commit -m "Initial LOL translate overlay"
git branch -M main
git remote add origin https://github.com/YOUR_NAME/lol-translate-overlay.git
git push -u origin main
```

## 后续可加功能

- OCR 框选屏幕文字识别
- DeepL 正式实现
- 常用 LOL 语句快捷按钮
- 打包成 `.exe`
