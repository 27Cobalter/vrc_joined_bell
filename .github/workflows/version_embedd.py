import os
import re

commit_hash = os.environ.get("GITHUB_SHA")
version_number = []
pattern = re.compile(".*v([0-9]+)\.([0-9]+).([0-9]+).")
version_number = re.match(pattern, os.environ.get("GITHUB_REF")).groups()
version_number_str = "{}.{}.{}".format(
    version_number[0], version_number[1], version_number[2]
)

print(
    f"""
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({version_number[0]}, {version_number[1]}, {version_number[2]}, 0),
    prodvers=({version_number[0]}, {version_number[1]}, {version_number[2]}, 0),
    mask=0x17,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904b0',
        [StringStruct(u'CompanyName', u'None'),
        StringStruct(u'FileDescription', u'vrc_joined_bell'),
        StringStruct(u'FileVersion', u'{version_number_str}'),
        StringStruct(u'InternalName', u'vrc_joined_bell'),
        StringStruct(u'LegalCopyright', u'Copyright 2020 vrc_joined_bell. All rights reserved.'),
        StringStruct(u'OriginalFilename', u'vrc_joined_bell'),
        StringStruct(u'ProductName', u'vrc_joined_bell'),
        StringStruct(u'ProductVersion', u'{version_number_str}'),
        StringStruct(u'CompanyShortName', u'None'),
        StringStruct(u'ProductShortName', u'vrc_joined_bell'),
        StringStruct(u'LastChange', u'{commit_hash}'),
        StringStruct(u'Official Build', u'1')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""
)
