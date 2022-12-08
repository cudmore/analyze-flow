## Revisiting this code, Nov 2022

The current linescan oir files have this

```
speedInformation lineSpeed #1	2.118
speedInformation lineSpeed #2	2.118
speedInformation lineSpeed #3	0.1267427122940431
```

But the following line has changed

```
# was
configuration scannerType #1 = Galvano

# is now
configuration scannerType = Galvano
```