There is a full book associated with the library<br>
[ReadTheDocs](https://github.com/rlabbe/filterpy)

First, install `filterpy`. This conveniently installs matplotlib, numpy, scipy automatically.
```bash
pip install filterpy
```
or
```bash
pip3 install filterpy
```
<details>
<summary>Click to expand for full list installed by filterpy.</summary>

```
contourpy==1.3.2
cycler==0.12.1
filterpy==1.4.5
fonttools==4.62.1
kiwisolver==1.5.0
matplotlib==3.10.8
numpy==2.2.6
packaging==26.0
pillow==12.2.0
pyparsing==3.3.2
python-dateutil==2.9.0.post0
scipy==1.15.3
six==1.17.0
```
</details><br>
Then:
```python
pip freeze > requirement.txt
```


In your Python file:
```python
from filterpy.kalman import ExtendedKalmanFilter
```
An EKF always needs to know:
- How big your state is
- How big your measurement is


