### 小鹤双拼 Ibus 配置
----

#### default.custom.yaml
```
patch:
  schema_list:
    - { schema: double_pinyin_flypy }
  "menu/page_size": 5   # 每頁候選數
  "punctuator/import_preset": symbols
  "punctuator/symbols":
    "/fs": [½, ‰, ¼, ⅓, ⅔, ¾, ⅒ ]
    "/bq": [😂️, 😅️, 😱️, 😭️, 😇️, 🙃️, 🤔️, 💊️, 💯️, 👍️, 🙈️, 💩️, 😈️ ]
    "/dn": [⌘, ⌥, ⇧, ⌃, ⎋, ⇪, , ⌫, ⌦, ↩︎, ⏎, ↑, ↓, ←, →, ↖, ↘, ⇟, ⇞]
    "/fh": [ ©, ®, ℗, ℠, ™, ℡, ␡, ♂, ♀, ☉, ☊, ☋, ☌, ☍, ☐, ☑︎, ☒, ☜, ☝, ☞, ☟, ✎, ✄, ♲, ♻, ⚐, ⚑, ⚠]
    "/xh": [ ＊, ×, ✱, ★, ☆, ✩, ✧, ❋, ❊, ❉, ❈, ❅, ✿, ✲]
  "punctuator/full_shape/%":
    - "%"
    - "‰"
    - "‱"
    - "％"
    - "°"
    - "℃"
  "punctuator/half_shape/%":
    - "%"
    - "‰"
    - "‱"
    - "％"
    - "°"
    - "℃"
  "punctuator/full_shape/*":
    - "*"
    - "＊"
    - "×"
    - "✱"
    - "★"
    - "☆"
    - "✩"
    - "✧"
    - "❋"
    - "❊"
    - "❉"
    - "❈"
    - "❅"
    - "✿"
    - "✲"
  "punctuator/full_shape/y":
    - "✓"
    - "✔"
  "punctuator/half_shape/n":
    - "✗"
    - "✘"
    - "✖"
    - "✕"

```

#### luna_pinyin.custom.yaml
```
# luna_pinyin.custom.yaml
#
# 【朙月拼音】模糊音定製模板
#   佛振配製 :-)
#
# 位置：
# ~/.config/ibus/rime  (Linux)
# ~/Library/Rime  (Mac OS)
# %APPDATA%\Rime  (Windows)
#
# 於重新部署後生效
#

patch:
  switches:                   # 注意缩进
    - name: ascii_mode
      reset: 0                # reset 0 的作用是当从其他输入法切换到本输入法重设为指定状态
      states: [ 中文, 西文 ]   # 选择输入方案后通常需要立即输入中文，故重设 ascii_mode = 0
    - name: full_shape
      states: [ 半角, 全角 ]   # 而全／半角则可沿用之前方案的用法。
    - name: simplification
      reset: 1                # 增加这一行：默认启用「繁→簡」转换。
      states: [ 漢字, 汉字 ]
  "speller/algebra":
    - erase/^xx$/
    - derive/^([zcs])h/$1/ 
    - derive/^([zcs])([^h])/$1h$2/ 
    - derive/^n/l/ 
    - derive/^l/n/ 
    - derive/^([bpmf])eng$/$1ong/ 
    - derive/([ei])n$/$1ng/ 
    - derive/([ei])ng$/$1n/ 
    - derive/^([jqxy])u$/$1v/
    - derive/^([aoe].*)$/o$1/
    - xform/^([ae])(.*)$/$1$1$2/
    - xform/iu$/Q/
    - xform/[iu]a$/W/
    - xform/er$|[uv]an$/R/
    - xform/[uv]e$/T/
    - xform/v$|uai$/Y/
    - xform/^sh/U/
    - xform/^ch/I/
    - xform/^zh/V/
    - xform/uo$/O/
    - xform/[uv]n$/P/
    - xform/i?ong$/S/
    - xform/[iu]ang$/D/
    - xform/(.)en$/$1F/
    - xform/(.)eng$/$1G/
    - xform/(.)ang$/$1H/
    - xform/ian$/M/
    - xform/(.)an$/$1J/
    - xform/iao$/C/
    - xform/(.)ao$/$1K/
    - xform/(.)ai$/$1L/
    - xform/(.)ei$/$1Z/
    - xform/ie$/X/
    - xform/ui$/V/
    - derive/T$/V/
    - xform/(.)ou$/$1B/
    - xform/in$/N/
    - xform/ing$/;/
    - xlit/QWRTYUIOPSDFGHMJCKLZXVBN/qwrtyuiopsdfghmjcklzxvbn/

```

#### squirrel.custom.yaml
```
patch:
  show_notifications_when: appropriate  # 状态通知，适当，也可设为全开（always）全关（never）
  "style/color_scheme": pithy # 选词皮肤
  preset_color_schemes:
    pithy:
      name: "简洁 / Pithy"
      author: "@hotoo"

      horizontal: false                                 # 水平排列
      inline_preedit: true                              # true: 单行显示，false: 双行显示
      candidate_format: "\u2005%c\u2005%@\u2005"        # 用 1/6 em 空格 U+2005 来控制编号 %c 和候选词 %@ 前后的空间。

      corner_radius: 0                                  # 候选条圆角
      border_height: 2                                  # 窗口边界高度，大于圆角半径才生效
      border_width: 2                                   # 窗口边界宽度，大于圆角半径才生效
      back_color: 0xFFFFFF                              # 候选条背景色
      border_color: 0xE0B693                            # 边框色
      font_face: "PingFangSC-Regular, H-SiuNiu"         # 候选词字体
      font_point: 19                                    # 候选字词大小
      text_color: 0x424242                              # 高亮选中词颜色
      label_font_face: "SimHei"                         # 候选词编号字体
      label_font_point: 18                              # 候选编号大小
      label_color: 0x9e9e9e                             # 预选栏编号颜色
      candidate_text_color: 0x000000                    # 预选项文字颜色
      text_color: 0x9e9e9e                              # 拼音行文字颜色，24位色值，16进制，BGR顺序
      comment_text_color: 0x999999                      # 拼音等提示文字颜色
      hilited_text_color: 0x9e9e9e                      # 高亮拼音 (需要开启内嵌编码)
      hilited_candidate_text_color: 0x000000            # 第一候选项文字颜色
      hilited_candidate_back_color: 0xfff0e4            # 第一候选项背景背景色
      hilited_candidate_label_color: 0x9e9e9e           # 第一候选项编号颜色
      hilited_comment_text_color: 0x9e9e9e              # 注解文字高亮

  # 關閉中文輸入
  # @see [http://code.google.com/p/rimeime/wiki/CustomizationGuide#在特定程序裏關閉中文輸入]
  #
  # Bundle Identifier 查找方法：
  # 右键『应用.app』-> 显示包内容
  # Contents/Info.plist -> BundleIdentifier
  #           Bundle Identifier
  app_options/com.apple.Xcode:
    ascii_mode: true
  app_options/org.vim.MacVim:
    ascii_mode: true
  app_options/com.google.Chrome:
    ascii_mode: true
  app_options/org.mozilla.firefox:
    ascii_mode: true
  app_options/com.apple.Safari:
    ascii_mode: true
  app_options/com.operasoftware.Opera:
    ascii_mode: true
  app_options/org.keepassx.keepassx:
    ascii_mode: true
  app_options/com.apple.Spotlight:
    ascii_mode: true

```


#### makefile
```
OS := $(shell uname)

ifeq ($(OS), Darwin)
	INSTALL_FLAG = "install-unix"
	INSTALL_DIR = "~/Library/Rime"
endif
ifeq ($(OS), Linux)
	INSTALL_FLAG = "install-unix"
	INSTALL_DIR = "~/.config/ibus/rime"
endif
ifeq ($(OS), Windows_NT)
	INSTALL_FLAG = "install-win"
	INSTALL_DIR = "%APPDATA%\Rime"
endif


install:
	@make $(INSTALL_FLAG)

install-unix:
	@eval "ln -s $(CURDIR)/default.custom.yaml     $(INSTALL_DIR)/default.custom.yaml"
	@eval "ln -s $(CURDIR)/luna_pinyin.custom.yaml $(INSTALL_DIR)/luna_pinyin.custom.yaml"
	@eval "ln -s $(CURDIR)/squirrel.custom.yaml    $(INSTALL_DIR)/squirrel.custom.yaml"

install-win:
	@eval "cp $(CURDIR)/default.custom.yaml     $(INSTALL_DIR)\default.custom.yaml"
	@eval "cp $(CURDIR)/luna_pinyin.custom.yaml $(INSTALL_DIR)\luna_pinyin.custom.yaml"
	@eval "cp $(CURDIR)/squirrel.custom.yaml    $(INSTALL_DIR)\squirrel.custom.yaml"

uninstall:
	@eval "rm $(INSTALL_DIR)/default.custom.yaml"
	@eval "rm $(INSTALL_DIR)/luna_pinyin.custom.yaml"
	@eval "rm $(INSTALL_DIR)/squirrel.custom.yaml"

```