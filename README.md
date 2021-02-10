# Programming vacancies compare

This script takes information about programming vacancies from 
- [API HeadHunter](https://api.hh.ru)
- [API SuperJob](https://api.superjob.ru)

and displays it into two tables.

### How to install

Taking information from [API HeadHunter](https://api.hh.ru) does not require any keys. To take information from 
[API SuperJob](https://api.superjob.ru) you need to get [SuperJob Secret key.](https://www.superjob.ru/auth/login/?returnUrl=https://api.superjob.ru/register/)
Put it into `.env` file, and assign Secret key to the `SUPER_JOB_API_KEY` variable.
It should look like this:

```
SUPER_JOB_API_KEY='v3.r.133631474.ba8f0ff3de0e13cbc771c1e2110f.c7a701f19f1c9455f917000c05ac173dcf'
```
Python3 should be already installed. 
Then use `pip` (or `pip3`, if there is a conflict with Python2) to install dependencies:
```
pip install -r requirements.txt
```

Run scripts in command line:
```
python3 main.py
```


### Project Goals
The code is written for educational purposes on online-course for web-developers [dvmn.org](https://dvmn.org)
