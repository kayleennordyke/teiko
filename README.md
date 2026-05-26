# Teiko Interview

## Table of Contents

- [Intructions to Run Code & Reproduce Outputs](#intructions-to-run-code--reproduce-outputs)
- [Link to the Dashboard](#link-to-the-dashboard)
- [Schema Design](#schema-design)
- [Brief Overview of Code Structure](#brief-overview-of-code-structure)
- [Thanks!](#thanks)

## Intructions to Run Code & Reproduce Outputs

In GitHub Codespaces, run from the project root:

```bash
make setup
make pipeline
make dashboard
```

`make setup` installs dependencies

`make pipeline` runs the full workflow (load_data.py & analysis.py)

`make dashboard` starts the local server for the interactive dashboard (via Streamlit)

## Link to the Dashboard
Open **http://localhost:8501** in the browser to view the dashboard.

## Schema Design

At initial glance, the data appeared to split into a hierachy of granularity. At the highest level, we have the project, then the subject/patient, and finally the individual treatments (most fine granularity). 

Each subject belongs to exactly one project. Looking through the raw data, there are only three projects, so I chose to have each subject linked to their respective study, using the subject_id as the primary key. 

For the patients table, I noted that every patient/subject will have characteristics associated with only that patient. Basically, this table is used to describe the traits of the individual patients. subject_id is the foreign key that links to the projects table.

Finally, for the treatments table, every treatment has their own configuration of cell types, when the treatment started, sample, etc. This is the finest granularity of the dataset due to every subject having multiple treatments. 

While projects and patients table would grow with hundreds of projects adding hundreds of new subjects and treatments, it would stay about one row per subject. The only thing that would grow by a greater amount is treatments. So, using this schema we only expect one table to increase by a large amount of rows. 

Just like this interview project, if there were various types of analytics to perform, I could easily join the tables on the foreign key that they all share (subject_id) to extract whatever cross-information I need.

## Brief Overview of Code Structure

The code is split into three python files: `analysis.py`, `load_data.py`, `dashboard.py`. 

`load_data.py` handles only Part 1, which reads in the CSV and cleans up missing values. It then loads the data into SQLite using `schema.sql` (which lays out the SQL schema).

Then for the analysis, I made a separate file `analysis.py` to keep files from getting too cluttered, and a clear area for the heavy duty analysis. This file answers all the interview questions from Part 2 to Part 4 including the bonus questions asking for the average number of B cells. This file includes both the queries and logic. I was not entirely sure if the auto grader was expecting saved tables (via csv) or just printing to the terminal, but I did both just in case. All output files are saved into the directory `outputs`.

For the dashboard, I used streamlit since I was familiar with it for my Capstone. All the dashboard code is contained in `dashboard.py`. The dashboard directly imports queries and functions from `analysis.py`.

The initial csv is already included in the repo: `cell-count.csv`.

Makefile is included for autograding purposed outlined in the interview prompt.

## Thanks!

Thank you to the hiring team for taking the time to review my repo. Would love to speak more on it. 