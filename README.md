## canvas-cli

`canvas-cli` is a small command-line tool for working with your NSU Canvas account. It lets you log in, list courses, view announcements, and sync course files to a local folder you choose.

---

**Key Features**
1. Login/logout and credential checks.
2. List courses and view announcements.
3. Configure a sync directory and course ignore list.
4. Sync course files to `Canvas/<course name>/Files`.
5. Sync course module to `Canvas/<course name>/Modules`.

---

**Quick Start**

* Create New Canvas Access Token From : <a>https://northsouth.instructure.com/profile/settings</a>


```bash
python canvas.py -help
python canvas.py -login
python canvas.py -syncmanager
python canvas.py -filesync
python canvas.py -modulesync
```

If you run the CLI with no arguments, it will guide you to log in or show the available commands once you’re authenticated.
