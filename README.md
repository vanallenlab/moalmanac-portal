# Molecular Oncology Almanac portal

Installation
```bash
conda create -y -n moalmanac-portal python=3.7
conda activate moalmanac-portal
pip install -r requirements.txt
```

Mac installation with Anaconda
```bash
conda create -y -n moalmanac-portal python=3.7
conda install -c conda-forge gcc pyicu
conda activate moalmanac-portal
pip install -r requirements.txt
```


sudo install libicu-dev for PYICU


libpcre3-dev