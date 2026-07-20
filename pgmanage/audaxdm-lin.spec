# -*- mode: python -*-

import os

# since pyinstaller does not have option to specify folders to exclude
# we use basic filtering
# https://github.com/orgs/pyinstaller/discussions/6126

exclude_patterns = [
  '.dist-info',
  '.py',
  'django/contrib/humanize',
  'django/contrib/gis',
  'django/contrib/flatpages',
  'django/contrib/sitemaps',
  'django/contrib/syndication',
  'django/contrib/admindocs',
]

block_cipher = None

data_files = [
  ('audaxdm.db','.'),
  ('config.py','.'),
  ('app/static/dist','app/static/dist'),
  ('app/static/plugins','app/static/plugins'),
  ('app/static/temp','app/static/temp'),
  ('app/include','app/include'),
  ('app/templates','app/templates'),
  ('app/plugins','app/plugins'),
]

a = Analysis(['pgmanage-server.py'],
             pathex=['app/include/'],
             binaries=[('/lib/x86_64-linux-gnu/libcrypt.so.1', '.')],
             datas=data_files,
             hiddenimports=['cheroot.ssl','cheroot.ssl.builtin','psycopg2','paramiko', 'pkg_resources.extern', 'cryptography.hazmat.primitives.kdf.pbkdf2', 'cryptography.x509'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['django.contrib.gis', 'django.contrib.sitemaps', 'django.contrib.flatpages', 'django.contrib.syndication', 'django.contrib.admindocs', 'django.contrib.humanize'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

# config.py gets removed by the next expression, keep it for restoring later
configpy = [entry for entry in a.datas if 'config.py' in entry[0]]
a.datas = [entry for entry in a.datas if not any(pattern in entry[0] for pattern in exclude_patterns)]
a.datas = a.datas + configpy

pyz = PYZ(a.pure, a.zipped_data,
            cipher=block_cipher)

exe = EXE(pyz,
         a.scripts,
         [],
         a.binaries,
         a.zipfiles,
         a.datas,
         name='audaxdm-server',
         debug=False,
         strip=False,
         upx=True,
         runtime_tmpdir=None,
         console=True )
