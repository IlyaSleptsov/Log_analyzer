# Log_analyzer

This repository contains analyzer for web-server logs and unittests for it. 
Analyzer counts the following metrics:

- count - the number of times the URL is encountered, the absolute value
- count_perc - the number of times the URL is encountered, as a percentage of the total number of requests
- time_sum - total $request_time for this URL, absolute value
- time_perc - total $request_time for this URL, as a percentage of the total $ request_time of all requests
- time_avg - the average $request_time for this URL
- time_max - the maximum $request_time for this URL
- time_med - the median $request_time for this URL

To run the program, enter the folliwng code:
```python
python3 log_analyzer.py
```
or next one, if you want to specify config:
```python
python3 log_analyzer.py --config <PATH_TO_CONFIG>
```
