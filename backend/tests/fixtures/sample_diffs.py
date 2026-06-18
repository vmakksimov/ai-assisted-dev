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
