"""
Python3.6+ only
"""
import re
from pathlib import Path

from pie import *



class env(env):
    @classmethod
    def _parse_lines(cls,ls):
        """Parses lines and returns a dict."""
        d={}
        for i,l in enumerate(ls,1):
            l=l.strip()
            # skip blank lines and comments
            if not l or l.startswith('#'): continue
            # ignore `set` and `export` and split into pre and post `=` parts
            mo=re.match(r'^(set\s+|export\s+)?(?P<key>[^=\s]+)\s*=(?P<value>.*)',l)
            if mo:
                d[mo.group('key')]=mo.group('value')
            else:
                raise Exception(f'Failed to parse line {i}: "{l}"')
        return d

    @classmethod
    def from_files(cls,*files):
        d={}
        # turn files into Path objects
        env_files=[Path(f) for f in files]
        # and filter out files that don't exist
        existing_env_files=[]
        for ef in env_files:
            if ef.exists():
                existing_env_files.append(ef)
            else:
                print(f'INFO: {ef} not found')
        # parse all existing files in order
        for p in existing_env_files:
            with p.open('r',encoding='utf-8') as fin:
                file_d=cls._parse_lines(fin.readlines())
                d.update(file_d)
        return cls(d)


    @classmethod
    def dump_env(cls):
        import os
        for k in sorted(os.environ.keys()):
            v=os.environ[k]
            print(f'{k}={v}')
