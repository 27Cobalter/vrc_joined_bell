# vrc_joined_bell
## これは何
- ~~VRCでワールドに人が入ってきたら音を鳴らすやつ~~
- VRCのログを見て特定のイベント時に音を鳴らすやつ

## ダウンロード
- https://github.com/27Cobalter/vrc_joined_bell/releases

## 自分で色々やりたい人向け
### 依存パッケージ
- pyyaml
```
$ pip install pyyaml pygame
```

### 実行方法
#### pythonで実行
- vrc_joined_bell.pyと同じ階層に設定ファイル`notice.yml`を配置して以下のコマンドを実行
```
$ python vrc_joined_bell.py
```
#### 実行ファイル生成
```
$ pyinstaller.exe vrc_joined_bell.py [-F -w]
  オプションはお好みで
  -F : ファイルを1つにまとめる
  -w : 実行時にウィンドウを表示しない(タスクマネージャーからkill)
```
dist以下に実行ファイルが生成されるのでexeファイルと同じ階層に設定ファイル`notice.yml`を配置してexeファイルを実行

## 設定ファイル
- timeのstartとendで通知音を鳴らしたくない時間を設定
- notices以下に取得したいイベントの正規表現(ログファイルでの形式)をevent，再生する音声ファイルのパス(実行ファイルからの相対パス，または絶対パス)をsoundとして列挙して`notice.yml`に記述
- 例
```notice.yml
# 通知音を鳴らしたくない時間
time:
  start: "00:00:00"
  end:   "06:00:00"
notices:
# invite
  - event: ".*?Received Notification:.*?type:invite.*"
    sound: "invite.wav"
# requestInvite
  - event: ".*?Received Notification:.*?type:requestInvite.*"
    sound: "reqInvite.wav"
# プレイヤー入場時
  - event: ".*?\\[NetworkManager\\] OnPlayerJoined .*"
    sound: "playerJoined.wav"
# プレイヤー退出時
  - event: ".*?\\[NetworkManager\\] OnPlayerLeft .*"
    sound: "playerLeft.wav"
```
