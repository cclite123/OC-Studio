"""Explicit stdlib & 3rd-party imports required by the external core/ submodule when frozen with PyInstaller."""

# Core submodule (core/Scripts/*) is bundled as data files so upstream updates stay untouched.
# PyInstaller cannot statically trace imports inside data files, so we list all stdlib/3rd-party
# modules used by core/ here to guarantee they are bundled in frozen builds.

import binascii  # noqa: F401
import certifi  # noqa: F401
import copy  # noqa: F401
import csv  # noqa: F401
import ctypes  # noqa: F401
import errno  # noqa: F401
import functools  # noqa: F401
import getpass  # noqa: F401
import glob  # noqa: F401
import gzip  # noqa: F401
import hashlib  # noqa: F401
import json  # noqa: F401
import os  # noqa: F401
import pathlib  # noqa: F401
import platform  # noqa: F401
import plistlib  # noqa: F401
import queue  # noqa: F401
import random  # noqa: F401
import re  # noqa: F401
import shlex  # noqa: F401
import shutil  # noqa: F401
import socket  # noqa: F401
import ssl  # noqa: F401
import subprocess  # noqa: F401
import sys  # noqa: F401
import tempfile  # noqa: F401
import threading  # noqa: F401
import time  # noqa: F401
import traceback  # noqa: F401
import urllib.error  # noqa: F401
import urllib.parse  # noqa: F401
import urllib.request  # noqa: F401
import uuid  # noqa: F401
import xml.etree.ElementTree  # noqa: F401
import zipfile  # noqa: F401
import zlib  # noqa: F401
