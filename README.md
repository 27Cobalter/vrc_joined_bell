# vrc_joined_bell
## これは何
- VRCでワールドに人が入ってきたら音を鳴らすやつ

## 利用方法
### pythonで実行
- vrc_joined_bell.pyと同じ階層に再生したい音声ファイル`sound.wav`を配置
```
$ python vrc_joined_bell.py
```
### exeで使う
```
$ pyinstaller.exe vrc_joined_bell.py [-F -w]
  オプションはお好みで
  -F : ファイルを1つにまとめる
  -w : 実行時にウィンドウを表示しない(タスクマネージャーからkill)
```
dist以下に実行ファイルが生成されるのでexeファイルと同じ階層に再生したい音声ファイル`sound.wav`を配置
