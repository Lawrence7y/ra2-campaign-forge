@echo off
rem 独立评审方实跑候选件 --selftest（零真机：该命令只跑离线单测，无进程访问）
python -I -X utf8 "D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112\e3_stack_sampler_candidate.py" --selftest 1>"D:\Project\ra2-campaign-forge\lead\re_d13_review_20261112\_review_selftest_stdout.txt" 2>"D:\Project\ra2-campaign-forge\lead\re_d13_review_20261112\_review_selftest_stderr.txt"
echo EXITCODE=%ERRORLEVEL%
