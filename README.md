# vrc_joined_bell
## これは何
- ~~VRCでワールドに人が入ってきたら音を鳴らすやつ~~
- VRCのログを見て特定のイベント時に音を鳴らすやつ

## 依存パッケージ
- pyyaml
```
$ pip install pyyaml
```

## 実行方法
### pythonで実行
- vrc_joined_bell.pyと同じ階層に設定ファイル`notice.yml`を配置して以下のコマンドを実行
```
$ python vrc_joined_bell.py
```
### 実行ファイル生成
```
$ pyinstaller.exe vrc_joined_bell.py [-F -w]
  オプションはお好みで
  -F : ファイルを1つにまとめる
  -w : 実行時にウィンドウを表示しない(タスクマネージャーからkill)
```
dist以下に実行ファイルが生成されるのでexeファイルと同じ階層に設定ファイル`notice.yml`を配置してexeファイルを実行

## 設定ファイル
- 取得したいイベントの正規表現(ログファイルでの形式)をkey，再生する音声ファイルのパス(実行ファイルからの相対パス，または絶対パス)をvalueとして`notice.yml`に記述
- 例
```notice.yml
# invite
".*?Received Notification:.*?type:invite.*": "sound.wav"
# requestInvite
".*?Received Notification:.*?type:requestInvite.*": "sound.wav"
# プレイヤー入場時
".*?\\[NetworkManager\\] OnPlayerJoined .*": "D:\\PATH_TO\\sound.wav"
# プレイヤー退出時
".*?\\[NetworkManager\\] OnPlayerLeft .*": "D:\\PATH_TO\\sound.wav"
```
