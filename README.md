# CS 112 Final Course Project — Summer 2026

Team members: 
Nathan Nii Adjei Anum- Role 1
Yidana Seli Sanid -Role 2
Janice Wetawuki Mpuah- Role 3
Edem Yaw Afanu -Role 4

## Folder structure

```
grid-network-analysis/   Component 1: data cleaning, EDA, NetworkX analysis, visualizations
  data/                  raw and cleaned CSVs (real data files are gitignored — see note below)
  notebooks/             Jupyter notebooks
  scripts/               the dataset-generation script + any reusable .py scripts

gridcare-lite/           Component 2: outage & maintenance desktop app
  gui/                   Tkinter/PyQt screens
  db/                    schema.sql, database setup scripts
  tests/                 test cases

clinic-care-lite/        Component 3: clinic admin & communication app
  app/                   Flask routes/models
  templates/              HTML templates
  static/                 CSS/JS
  tests/                 test cases

docs/                    reports, ER diagrams, data dictionaries, user guides
diagrams/                architecture / class / data-flow diagrams
```

> Note: `.db` files and generated data are excluded via `.gitignore` by default. If you actually
> want to share small CSVs through Git, add specific exceptions in `.gitignore` — just don't commit
> large or regenerable files.

## Getting started (do this once)

```bash
git clone <your-repo-url>
cd cs112-final-project
```

## Daily workflow (do this every time you work)

1. **Get the latest code before you start:**
   ```bash
   git checkout main
   git pull
   ```

2. **Create a branch for whatever you're working on:**
   ```bash
   git checkout -b feature/short-description
   ```
   Examples: `feature/outage-form`, `feature/login-auth`, `data/clean-substations`

3. **Work, then save checkpoints as you go:**
   ```bash
   git add .
   git commit -m "Short description of what changed"
   ```

4. **Push your branch to GitHub:**
   ```bash
   git push -u origin feature/short-description
   ```
   (After the first push, `git push` alone works.)

5. **Open a Pull Request on GitHub** comparing your branch to `main`. Tag a teammate to review it.

6. **After approval, merge the PR on GitHub**, then locally:
   ```bash
   git checkout main
   git pull
   git branch -d feature/short-description
   ```

## If you get a merge conflict

Git will mark the conflicting spot in the file like this:

```
<<<<<<< HEAD
your version
=======
their version
>>>>>>> feature/their-branch
```

Open the file, decide what the code should actually say, delete the `<<<<<<<`, `=======`,
`>>>>>>>` lines, then:

```bash
git add <the file>
git commit
```

## Team norms (edit as your team agrees)

- Branch names: `feature/...`, `fix/...`, `data/...`
- Every PR needs at least 1 review before merging
- Push at least once a day, even mid-feature
- Whoever opens a PR is responsible for merging it once approved
