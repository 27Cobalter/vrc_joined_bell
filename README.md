# vrc_joined_bell
# 注意
- 4/2のアップデートでデフォルトで`OnPlayerJoined`, `OnPlayerLeft`が出力されなくなったためSteamから`プロパティ->起動オプションを設定`を開いて`--enable-sdk-log-levels`を追加してください
## これは何
- ~~VRCでワールドに人が入ってきたら音を鳴らすやつ~~
- VRCのログを見て特定のイベント時に音を鳴らすやつ

## ダウンロード
- https://github.com/27Cobalter/vrc_joined_bell/releases

## 自分で色々やりたい人向け
- ~~CeVIOのDLLが32bitのためCeVIOの使用時には32bit版pythonを利用する必要あり~~
- CS7より64bit対応
### 依存パッケージ
- pyyaml
```
$ pip install pyyaml
```
- pygame
```
$ pip install pygame
```
- pythonnet(CeVIOを動かすとき)
```
$ pip install pythonnet
```

### test 
```
pip install pytest freezegun
ENV=test pytest vrc_joined_bell.py 
```

### 実行方法
#### pythonで実行
- `vrc_joined_bell.py`と同じ階層に設定ファイル`notice.yml`を配置して以下のコマンドを実行
```
$ python vrc_joined_bell.py
```
#### 実行ファイル生成
```
$ pyinstaller.exe vrc_joined_bell.py -F --hidden-import=clr
```
dist以下に実行ファイルが生成されるのでexeファイルと同じ階層に設定ファイル`notice.yml`を配置してexeファイルを実行

## 設定ファイル
- silent_timeのstartとendで通知音を鳴らしたくない時間を設定
- notices以下に取得したいイベントの正規表現(ログファイルでの形式)をevent，再生する音声ファイルのパス(実行ファイルからの相対パス，または絶対パス)をsoundとして列挙して`notice.yml`に記述
- CeVIO使用時はmessageを定義することで`正規表現の1つめのグループ`+`message`が再生される
- dllにCeVIOのDLL(`CeVIO.Talk.RemoteService.DLL`)が配置してあるディレクトリを指定 デフォルトでは`C:\Program Files\CeVIO\CeVIO Creative Studio (64bit)`
- 例
```notice.yml
# サイレントモードの設定
silent:
  # サイレントモードの振る舞いの設定
  # ignore は通知を止める
  # volume_down は音量を下げる
  behavior: 'volume_down' # or ignore
  # サイレントモード時で volume_down 時の音量の値
  volume: 0.05
  # 時刻でサイレントモードを有効にする時間
  time:
    # 開始時刻
    start: '00:00:00'
    # 終了時刻
    end:   '06:00:00'
  
# サイレントモードの除外設定
  exclude:
    # 曜日
    days_of_week:
      - "Sat"
      - "Sun"
    # ユーザー（マッチグループ1つめ）
    match_group: # user
      - 27Cobalter
      - bootjp／ぶーと
  # web server経由での on/offを可能にするか
  toggle_server: on
  # listen するホスト名
  host: 127.0.0.1
  # ポート
  port: 80

notices:
# invite
  - event: '.*?Received Notification:.*?type:invite.*'
    sound: 'invite.wav'
# requestInvite
  - event: '.*?Received Notification:.*?type:requestInvite.*'
    sound: 'reqInvite.wav'
# プレイヤー入場時
  - event: '.*?\[NetworkManager\] OnPlayerJoined (.*)'
    sound: 'playerJoined.wav'
    message: 'さんが入室しました'
# プレイヤー退出時
  - event: '.*?\[NetworkManager\] OnPlayerLeft (.*)'
    sound: 'playerLeft.wav'
    message: 'さんが退出しました'
# CeVIOを使う場合に記述
# cevio:
#   cast: 'IA'
#   max_phonemes: 16 # マッチしたグループの音素の数がこれ以下のときCeVIOで読む
#   dll: 'C:\Program Files\CeVIO\CeVIO Creative Studio (64bit)'
```
