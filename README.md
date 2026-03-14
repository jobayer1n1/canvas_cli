## canvas-cli

`canvas-cli` is a small command-line tool for working with your Canvas account. It lets you log in, list courses, view announcements, and sync course files to a local folder you choose.

**Key Features**
1. Login/logout and credential checks.
2. List courses and view announcements.
3. Configure a sync directory and ignore list.
4. Sync course files to `Canvas/<course name>/files`.

**Quick Start**
```bash
python canvas.py -help
python canvas.py -login
python canvas.py -syncmanager
python canvas.py -filesync
```

If you run the CLI with no arguments, it will guide you to log in or show the available commands once you’re authenticated.
