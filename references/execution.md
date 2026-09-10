# 执行指南

助手运行命令，制作方只做本步的人类判断。下文 PROJECT 表示本单真实绝对路径，运行前替换；提示词交付中不能留下占位符。命令从本 Skill 根目录执行。Python 3.9+；素材存放于独立项目目录，不能写到公开 Skill 内。遵守宿主外盘规则。

## 状态和版本

```bash
python3 scripts/wizard.py init PROJECT
python3 scripts/wizard.py summary PROJECT
python3 scripts/wizard.py prepare PROJECT --step 1 --files FACTS.md
python3 scripts/wizard.py approve PROJECT --step 1 --by producer --evidence '制作方实际回复的确认依据'
python3 scripts/wizard.py validate PROJECT
```

`prepare` 登记当前版本，`approve` 仅在收到对应回复后运行。第 3 步角色用 `couple`；第 14 步先 `producer` 再 `couple`，其余为 `producer`。进入下一步自动推进。不能把示例依据原样登记，不能手改状态跳过步骤。

`--files` 应含本步全部选用文件及决定它们含义的清单；尤其第 3 步 SCRIPT.txt，第 5 步旁白，第 6 步 SHOT_PLAN.json，第 7/8 步原图，第 9 步选用视频，第 11 步试听和 .mix.json，第 12 步完整主混音。记录技术 QC 和人类反馈为独立文件，不把 API 回执当成人类确认。

变更已确认材料，先保留旧文件，再回退：

```bash
python3 scripts/wizard.py reopen PROJECT --step 8 --affected 9 13 14 --reason 'S04 换图，需要重做该镜视频与成片'
```

这会使 8、9、13、14 待复核，保留其他通过项。不传 `--affected` 则从该步到结尾全部待复核。再确认时若中间步骤仍通过会跳至下一未确认步骤。文件丢失或变化触发校验失败时，用 reopen 记录变化，不修改旧指纹掩盖问题。

## 写作包和视频包

```bash
python3 scripts/wizard.py writing-pack PROJECT --prompt WRITING_PROMPT.txt --out writing-v1.zip
python3 scripts/wizard.py video-pack PROJECT --manifest VIDEO_PACK.json --out video-v1.zip
```

写作包须在第 2 步生成；交 ZIP，同时直接给可打开复制的全文文件。助手负责把事实、风格、篇幅、事实边界、完整输出要求全部写入实际文本。工具只能拦常见占位符，不能代替内容审查。

首帧会用 Pillow 实际解码验证，缺依赖时先安装再打包。

第 6 步登记的 SHOT_PLAN.json 最小结构为 `{"shots":[{"id":"S01"},{"id":"S02"}]}`，实际每镜补齐 visuals.md 要求的事实、旁白时间和动作字段。第 9 步的 VIDEO_PACK.json：

```json
{"plan":"SHOT_PLAN.json","shots":[
  {"id":"S01","image":"images/S01-v2.png","prompt":"prompts/S01-video.txt"},
  {"id":"S02","image":"images/S02-v1.png","prompt":"prompts/S02-video.txt"}
]}
```

镜号必须与已确认分镜一致，图片必须来自 7/8 步确认版本。ZIP 内实际图片＋本镜提示词，以及使用说明、SHA256 清单。提示词应明确首帧动作对应，不能仅复制图片词。视频返回后核对镜号、原图和选版，再确认第 9 步。

## 按需配置与本地媒体工具

```bash
python3 scripts/media.py doctor
```

仅显示配置是否存在，不输出密钥。使用前确认本单调用范围和收费供应商；不因有密钥自动获授权。变量：Kimi 用 `MOONSHOT_API_KEY`，可选 `MOONSHOT_MODEL`（默认 kimi-k3）、`MOONSHOT_BASE_URL`（仅官方地址）；豆包用 `DOUBAO_API_KEY`，或 `DOUBAO_APP_ID`＋`DOUBAO_ACCESS_KEY`，可选 `DOUBAO_RESOURCE_ID`（默认 seed-tts-2.0）。按账户实际服务配置，不能乱试资源 ID。

```bash
python3 scripts/media.py kimi PROJECT --prompt WRITING_PROMPT.txt --out SCRIPT-draft.txt --authorized
python3 scripts/media.py tts PROJECT --text VO_EXCERPT.txt --instructions VO_DIRECTION.txt --voice ACCOUNT_VOICE_ID --out voice-option-1.mp3 --authorized
python3 scripts/media.py probe PROJECT/voice-option-1.mp3
```

`--authorized` 是助手对已经取得授权的登记，不是自动产生授权；不要主动将实际密钥写入命令、GitHub、ZIP 或聊天。试听调用在第 4 步，完整旁白在第 5 步；沿用已选音色、指导和语速。原始服务时间戳保存在同名 .timing.json，需核查后才能成为 VO_TIMING.json。

第 4 步选定后，助手生成并随本步登记 VOICE_SELECTION.json：`voice` 为实际音色 ID，`rate` 为语速整数，`instructions` 为指导文件路径，`instructions_sha256` 为该文件实际 SHA256，`source_script` 为第 3 步 SCRIPT.txt 路径，`source_script_sha256` 为该稿实际 SHA256。第 5 步默认读取此文件（可用 `--selection` 指定），拒绝未经确认的新正文或不同音色/情绪/语速。先 `prepare` 登记包括选择表的本步文件，再根据真实选择回复 `approve`。

视频和音乐外部 API 未内置通用猜测接口。使用可用工具/官方文档适配用户指定服务；没有时交付手动包并接回文件。**任何路径都不能在 Codex 内执行生图。**

本地混音、剪辑需 FFmpeg、ffprobe、Pillow、中文字体。按宿主提供的依赖优先使用；缺失才引导安装并在当前对话继续。FFmpeg 可设置 `FFMPEG_BIN`/`FFPROBE_BIN`，字体可设置 `WEDDING_FONT` 为具体中文字体文件。Pillow 用 `python3 -m pip install Pillow`（使用虚拟环境时在该环境内）。路径带空格要正确引用。

## 混音与组装

```bash
python3 scripts/media.py mix PROJECT --voice audio/voice-final.wav --music audio/music-arranged.wav --start 12 --length 15 --gain 0.16 --out audio/mix-sample-1.wav
python3 scripts/media.py mix PROJECT --voice audio/voice-final.wav --music audio/music-arranged.wav --gain 0.16 --out audio/mix-full.wav
python3 scripts/media.py assemble PROJECT --plan EDIT_PLAN.json --out film-preview-v1.mp4
```

样例时间和音量必须按本单调整。旁白必须是第 5 步已确认文件；第 12 步使用第 11 步试听登记的声轨和参数。音乐长度需覆盖主旁白；延展和剪接在样本确认前安排妥当。

EDIT_PLAN.json 是可修改的剪辑工程，和原素材一起保留；调用同一工具即可重出，不声称它是剪映/Pr 原生工程。示意结构：

```json
{
  "storyboard":"SHOT_PLAN.json",
  "audio":"audio/mix-full.wav","width":1920,"height":1080,"fps":24,
  "shots":[
    {"id":"S01","file":"videos/S01-v1.mp4","in":0,"out":4,"start":0,"end":4},
    {"id":"S02","file":"videos/S02-v2.mp4","in":1,"out":5,"start":4,"end":8}
  ],
  "cues":[{"start":0.3,"end":3.7,"text":"本单已确认旁白的第一句"},
          {"start":4.2,"end":7.7,"text":"本单已确认旁白的第二句"}]
}
```

助手从真实音频与选定视频生成时间表；必须引用第 6 步确认的分镜表，每个已确认镜号按顺序出现一次，删镜或改顺序先重新确认分镜；字幕正文来自确认文案，断句、称呼和同步人工复核。切点对齐帧率；最后一个切点按最近帧取整，允许半帧内差异，完整音轨保持原长；镜头总长匹配实际主音轨，含留白；源区间不能超过素材。支持直切、适度变速、等比留边、字幕烧录，避免为炫技使用复杂转场。其他效果可使用宿主现有剪辑能力，但仍遵守批准版本和验收。

assemble 仅允许第 13/14 步，检查第 9 步视频及第 12 步音轨指纹，输出 MP4、同名 SRT 和技术 QC。它不会自动批准预览或交付。字幕可能因过长被拒绝，应按语义拆段，不缩成难读小字。最终交付附上实际 EDIT_PLAN.json、素材映射和使用说明。
