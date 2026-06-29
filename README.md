# canvas-cli

`canvas-cli` is a small command-line tool for your NSU Canvas account. It lets you sync course files, modules with your local computer and has some useful commands.

---

**Key Features**
1. Login/logout and credential checks.
2. List courses and view announcements.
3. Configure a sync directory and course ignore list.
4. Sync course files to `Canvas/<course name>/Files/<Canvas folder structure>`.
5. Sync course modules to `Canvas/<course name>/Modules`, while keeping the real file data in `Files/` and linking modules back to it.
6. Download single files by Canvas file id.
7. Switch the current terminal working directory to the Canvas sync directory.
8. Instantly access your local canvas files.

---

**Quick Start**

* Create New Canvas Access Token From : <a>https://northsouth.instructure.com/profile/settings</a>
* run `canvas -li [access_token]` to log in directly
* or run `canvas -li -g [jobayer1n1/repo/path]` to fetch from GitHub
* or run `canvas -li -clp [clip_id]` to fetch from cl1p
* Use Available Cmds

***To access canvas-cli from anywhere add canvas_cli directory to your PATH***

---

# Available Commands

Here is the complete list of available instructions and their shortcuts:

| Command | Alias | Description |
| :--- | :--- | :--- |
| `canvas --login` | `-li` | Log in to your canvas account using API token |
| `canvas --logout` | `-lo` | Log out of your canvas account |
| `canvas --help` | `-h` | See all commands and their usage |
| `canvas --courses` | `-c` | Get all your enrolled courses |
| `canvas --showfile [courseName]` | `-sf` | Show all file ids and names for a course |
| `canvas --downloadfile [fileId ...]` | `-df` | Download one or more files by Canvas file id, skipping files already downloaded fully |
| `canvas --announcements` | `-a` | Get all your announcements |
| `canvas --fetch` | `-f` | Fetch and refresh local Canvas enrollment metadata |
| `canvas --syncmanager` | `-sm` | Configure the syncing directory and course ignorelist |
| `canvas --filesync [courses...]` | `-fs` | Syncs all not ignored (or specified) course files to your local directory |
| `canvas --modulesync [courses...]` | `-ms` | Syncs all not ignored (or specified) course modules to your local directory using shared file links |
| `canvas --switch-current-working-directory` | `-scwd` | Switches the current shell directory to the Canvas sync directory |
| `canvas --open` | `-o` | Opens the local Canvas sync directory |
| `canvas --reset` | `-r` | Reset all configurations and data |

## Using -fs or -ms
To sync only specific courses, you can pass their names or codes as arguments:
```bash
canvas --filesync CSE331 PHY107
canvas --modulesync ENG103
```

## File Layout
Canvas CLI stores course files once in the course `Files/` tree and reuses them from `Modules/` with symlinks.

Example layout:
```text
Canvas/
  CSE323/
    Files/
      Week 1/
        a.txt
    Modules/
      Module 1/
        a.txt -> ../Files/Week 1/a.txt
```

This means:
- `filesync` writes the real file into `Files/`
- `downloadfile` writes the real file into `Files/`
- `modulesync` creates a module entry that points to the cached file

## Sync Output
The sync commands now use a staged progress format:

- `filesync`
  - `[OnGoing] a.txt [downloading] [downloaded]`
  - `[OnGoing] a.txt [resumeDownloading] [resumeFailed] [freshDownload] [downloaded]`
  - `[Skipped] a.txt [FileFound]`

- `downloadfile`
  - same staged output as `filesync`

- `modulesync`
  - downloads or reuses the cached file in `Files/`
  - creates a symlink inside `Modules/<module>/...`

## Using `-df`
You can download one file or several files in a single command:
```bash
canvas -df 12345
canvas -df 12345 67890 24680
```
If a file is already fully downloaded at the target location, Canvas CLI skips it and moves on to the next file id.

## Using the Ignorelist:

You can interactively configure an **Ignorelist** using the `canvas --syncmanager` command. When you have courses added to your ignorelist, running `canvas --filesync` or `canvas --modulesync` without any arguments will sync **all enrolled courses EXCEPT the ones on your ignorelist**.


## Using `--open` cmd:

Works for both files and modules.
| Command | Function | Example |
| :--- | :--- | :---|
| `-o CourseName` | open a specific course folder | -o MAT361 |
| `-o CourseName -m` | open that course modules | -o MAT361 -m |
| `-o CourseName -m {arg}` | open modules/{arg} | -o MAT361 -m week1 |

## Switching the Current Directory

### Windows cmd
Use the batch launcher so the current terminal directory changes in place:
```bat
canvas -scwd
```

### Linux bash/zsh
Source the shell helper once in your session, then run the same command:
```bash
source /path/to/canvas_cli/canvas.sh
canvas -scwd
```

If the sync directory is not configured yet, run `canvas --syncmanager` first.

---
