## canvas-cli

`canvas-cli` is a small command-line tool for working with your NSU Canvas account. It lets you sync course files, modules with you local computer and has some daily usage canvas commands.

---

**Key Features**
1. Login/logout and credential checks.
2. List courses and view announcements.
3. Configure a sync directory and course ignore list.
4. Sync course files to `Canvas/<course name>/Files`.
5. Sync course module to `Canvas/<course name>/Modules`.
6. Instantly access your local canvas files.

---

**Quick Start**

* Create New Canvas Access Token From : <a>https://northsouth.instructure.com/profile/settings</a>

***To access canvas-cli from anywhere add canvas_cli directory to your PATH***
```bash
canvas --help
canvas --login
canvas --syncmanager
canvas --filesync
canvas --modulesync
canvas --open
```

---

**Available Commands**

Here is the complete list of available instructions and their shortcuts:

| Command | Alias | Description |
| :--- | :--- | :--- |
| `canvas --login` | `-li` | Log in to your canvas account using API token |
| `canvas --logout` | `-lo` | Log out of your canvas account |
| `canvas --help` | `-h` | See all commands and their usage |
| `canvas --courses` | `-c` | Get all your enrolled courses |
| `canvas --announcements` | `-a` | Get all your announcements |
| `canvas --fetch` | `-f` | Fetch and refresh local Canvas enrollment metadata |
| `canvas --syncmanager` | `-sm` | Configure the standard syncing directory |
| `canvas --filesync [courses...]` | `-fs` | Syncs all (or specified) course files to your local directory |
| `canvas --modulesync [courses...]`| `-ms` | Syncs all (or specified) course modules to your local directory |
| `canvas --open` | `-o` | Opens the local Canvas sync directory |
| `canvas --reset` | `-r` | Reset all configurations and data |

**Example:**
To sync only specific courses, you can pass their names or codes as arguments:
```bash
canvas --filesync CSE331 PHY107
canvas --modulesync ENG103
```

---
