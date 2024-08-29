import pandas as pd

test = pd.DataFrame()
d = {'cool': 12, "be": 123213}
f = {"be": 11}

a = pd.DataFrame.from_dict([d, f])

for i in range(821, 829):
    print(i)