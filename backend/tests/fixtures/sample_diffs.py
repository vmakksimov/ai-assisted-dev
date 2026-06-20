"""Sample diffs used across tests."""

from __future__ import annotations

VALID_DIFF = """\
diff --git a/app/auth.py b/app/auth.py
index 1a2b3c4..5d6e7f8 100644
--- a/app/auth.py
+++ b/app/auth.py
@@ -10,7 +10,9 @@ def login(username, password):
-    user = db.query(f"SELECT * FROM users WHERE name = '{username}'")
+    user = db.query("SELECT * FROM users WHERE name = :name", name=username)
     if user and user.password == password:
-        return True
+        token = create_token(user)
+        return token
     return None
"""

WHITESPACE_ONLY_DIFF = """\
diff --git a/README.md b/README.md
index aaa..bbb 100644
--- a/README.md
+++ b/README.md
@@ -1,2 +1,2 @@
-Hello
+Hello
"""

NOT_A_DIFF = "This is just some prose with no diff headers or hunks at all."

EMPTY_DIFF = "   \n  \n"

# A realistic multi-file `git diff origin/develop...HEAD` style output: a normal
# text change plus a pure rename (no @@ / +++ / --- lines for the renamed file).
GIT_DIFF_WITH_RENAME = """\
diff --git a/app/auth.py b/app/auth.py
index 13b04a8..453f416 100644
--- a/app/auth.py
+++ b/app/auth.py
@@ -1,2 +1,5 @@
-def login():
+def login(username, password):
+    pass
+
+def extra():
     pass
diff --git a/app/old_name.py b/app/new_name.py
similarity index 100%
rename from app/old_name.py
rename to app/new_name.py
"""

# A diff that is *purely* a rename with no other files (no @@, no +++/---).
PURE_RENAME_ONLY_DIFF = """\
diff --git a/app/old_name.py b/app/new_name.py
similarity index 100%
rename from app/old_name.py
rename to app/new_name.py
"""

# A diff that is purely a file-mode change.
MODE_CHANGE_ONLY_DIFF = """\
diff --git a/run.sh b/run.sh
old mode 100644
new mode 100755
"""

# A diff with a binary file change (no textual hunks).
BINARY_ONLY_DIFF = """\
diff --git a/logo.png b/logo.png
index 1111111..2222222 100644
Binary files a/logo.png and b/logo.png differ
"""

# `git diff` output with ANSI SGR color codes (e.g. `color.ui=always`, or color
# surviving a terminal copy-paste) prefixing every line, including structural
# headers. This previously caused a false-negative "not a unified diff" rejection.
ANSI_COLORED_DIFF = (
    "\x1b[1mdiff --git a/app/auth.py b/app/auth.py\x1b[m\n"
    "\x1b[1mindex 13b04a8..453f416 100644\x1b[m\n"
    "\x1b[1m--- a/app/auth.py\x1b[m\n"
    "\x1b[1m+++ b/app/auth.py\x1b[m\n"
    "\x1b[36m@@ -1,2 +1,5 @@\x1b[m\n"
    "\x1b[31m-def login():\x1b[m\n"
    "\x1b[32m+\x1b[m\x1b[32mdef login(username, password):\x1b[m\n"
)

# Simulates a Windows PowerShell `git diff origin/develop...HEAD > review.diff`
# redirect, which writes the file as UTF-16 LE with a BOM (`FF FE ...`). If that
# byte stream is later decoded as UTF-8/Latin-1 instead of UTF-16 before reaching
# the parser, the result is a leading BOM character (`﻿`) plus a stray `\x00`
# NUL byte interleaved between every original ASCII character. We synthesize that
# exact mis-decoded shape here: a normal diff with `\x00` inserted after each
# character and a leading BOM, mirroring what a naive UTF-8/Latin-1 decode of a
# UTF-16 LE byte stream produces.
_UTF16_MISDECODE_SOURCE = """\
diff --git a/app/auth.py b/app/auth.py
index 1a2b3c4..5d6e7f8 100644
--- a/app/auth.py
+++ b/app/auth.py
@@ -10,7 +10,9 @@ def login(username, password):
-    user = db.query(f"SELECT * FROM users WHERE name = '{username}'")
+    user = db.query("SELECT * FROM users WHERE name = :name", name=username)
     if user and user.password == password:
-        return True
+        token = create_token(user)
+        return token
     return None
"""
UTF16_MISDECODED_DIFF = "﻿" + "\x00".join(_UTF16_MISDECODE_SOURCE)
