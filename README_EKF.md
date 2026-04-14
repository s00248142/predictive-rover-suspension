First, install `filterpy`
There is a full book associated with the library<br>
[ReadTheDocs](https://filterpy.readthedocs.io/en/latest/kalman/ExtendedKalmanFilter.html#id2)
```bash
pip3 install filterpy
```
In your Python file:
```python
from filterpy.kalman import ExtendedKalmanFilter
```
An EKF always needs to know:
- How big your state is
- How big your measurement is


